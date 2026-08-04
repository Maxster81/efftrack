"""Router amministrativo (Fase 12d).

Router protetto da `require_admin`. Espone:
- GET /admin            → dashboard di benvenuto (statistiche future)
- GET /admin/records    → tabella di TUTTI i record (no form, con export)
- GET /admin/records/export → export CSV di tutti i record
- GET /admin/users      → lista utenti (sola visualizzazione)
- GET /admin/users/{id}/edit → pagina di modifica per singolo utente
- GET /admin/lookup     → gestione lookup (clienti, gruppi, attività)

Protezioni:
- admin non può auto-declassarsi, auto-eliminarsi, né eliminare l'ultimo admin
- lookup con record associati in effort_entries non eliminabili
"""
from __future__ import annotations

import csv
import io
import logging
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.config import APP_NAME, APP_VERSION, AUTH_ENABLED, TEMPLATES_DIR, USER_DELETE_GRACE_DAYS
from app.core.permissions import require_admin
from app.db import get_db
from app.models import Activity, Client, EffortEntry, Group, User
from app.models.effort_entry import utcnow
from app.schemas.effort import LookupCreate, PasswordChange, RoleChange, UserCreate
from fastapi.templating import Jinja2Templates
from passlib.hash import bcrypt

logger: logging.Logger = logging.getLogger(__name__)

templates: Jinja2Templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

router: APIRouter = APIRouter(prefix="/admin", tags=["admin"])

# Nomi dei mesi in italiano.
_MESI_ITALIANI = [
    "", "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
    "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre",
]


def _sidebar_items() -> list[dict[str, str]]:
    """Voci della sidebar dell'area admin (Fase 12d)."""
    return [
        {"label": "Dashboard", "href": "/admin"},
        {"label": "Registrazioni", "href": "/admin/records"},
        {"label": "Gestione Utenti", "href": "/admin/users"},
        {"label": "Gestione Lookup", "href": "/admin/lookup"},
    ]


def _base_context(request: Request, current_username: str, active: str = "") -> dict:
    """Contesto condiviso per i template dell'area admin."""
    return {
        "app_name": APP_NAME,
        "app_version": APP_VERSION,
        "phase": "Fase 12d — Pannello Admin",
        "current_username": current_username,
        "auth_enabled": AUTH_ENABLED,
        "is_admin": True,
        "sidebar_items": _sidebar_items(),
        "active": active,
    }


@router.get("", response_class=HTMLResponse, name="admin_dashboard")
async def admin_dashboard(
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> HTMLResponse:
    """Dashboard admin (per ora benvenuto; statistiche future)."""
    return templates.TemplateResponse(
        request=request,
        name="admin_dashboard.html",
        context=_base_context(request, admin.username, "dashboard"),
    )


@router.get("/records", response_class=HTMLResponse, name="admin_records")
async def admin_records(
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
    month: str | None = None,
) -> HTMLResponse:
    """Tabella di tutti i record del sistema (no form, con filtro/export)."""
    month_stmt = (
        select(func.strftime("%Y-%m", EffortEntry.work_date).label("month"))
        .distinct()
        .order_by(func.strftime("%Y-%m", EffortEntry.work_date).desc())
    )
    month_rows = db.execute(month_stmt).scalars().all()
    month_options: list[tuple[str, str]] = []
    for m in month_rows:
        anno, num = m.split("-")
        month_options.append((m, f"{_MESI_ITALIANI[int(num)]} {anno}"))

    stmt = (
        select(EffortEntry)
        .options(
            selectinload(EffortEntry.client),
            selectinload(EffortEntry.group),
            selectinload(EffortEntry.activity),
            selectinload(EffortEntry.user),
        )
        .order_by(EffortEntry.work_date.desc())
    )
    if month:
        stmt = stmt.where(func.strftime("%Y-%m", EffortEntry.work_date) == month)
    records = db.execute(stmt).scalars().all()

    ctx = _base_context(request, admin.username, "records")
    ctx.update({"records": records, "month_options": month_options, "selected_month": month})
    return templates.TemplateResponse(
        request=request,
        name="admin_records.html",
        context=ctx,
    )


@router.get("/records/export", response_class=StreamingResponse, name="admin_records_export")
async def admin_records_export(
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
    month: str | None = None,
) -> StreamingResponse:
    """Esporta in CSV tutti i record del sistema (solo admin)."""
    stmt = (
        select(EffortEntry)
        .options(
            selectinload(EffortEntry.client),
            selectinload(EffortEntry.group),
            selectinload(EffortEntry.activity),
            selectinload(EffortEntry.user),
        )
        .order_by(EffortEntry.work_date.asc())
    )
    if month:
        stmt = stmt.where(func.strftime("%Y-%m", EffortEntry.work_date) == month)
    records = db.execute(stmt).scalars().all()

    filename = f"effort_admin_{month or 'tutti'}.csv"
    logger.info("Export CSV admin (record=%d, mese=%s)", len(records), month or "tutti")
    return StreamingResponse(
        iter([_build_csv(records)]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _build_csv(records: list[EffortEntry]) -> str:
    """Costruisce il contenuto CSV (con BOM UTF-8) dai record di effort."""
    header = ["Data", "Cliente", "Gruppo", "Attività", "Utente", "Ore", "Note", "Descrizione attività"]
    buffer = io.StringIO()
    buffer.write("\ufeff")
    writer = csv.writer(buffer)
    writer.writerow(header)
    for r in records:
        writer.writerow([
            r.work_date.strftime("%d/%m/%Y"),
            r.client.name,
            r.group.name,
            r.activity.name,
            r.user.username if r.user is not None else "",
            r.hours_spent,
            r.notes or "",
            r.description or "",
        ])
    return buffer.getvalue()


# --------------------------------------------------------------------------
# Gestione utenti
# --------------------------------------------------------------------------

def _format_last_login(value: datetime | None) -> str:
    if value is None:
        return "—"
    return value.strftime("%d/%m/%Y %H:%M")


def _user_stats(db: Session, user_id: int) -> int:
    return db.execute(
        select(func.count()).select_from(EffortEntry).where(EffortEntry.user_id == user_id)
    ).scalar() or 0


def _days_since(value: datetime | None) -> int | None:
    """Giorni trascorsi da un timestamp (None se assente)."""
    if value is None:
        return None
    return (utcnow() - value).days


def _can_delete_user(u: User) -> bool:
    """True se l'utente è disabilitato da almeno `USER_DELETE_GRACE_DAYS` giorni."""
    if not u.disabled or u.disabled_at is None:
        return False
    return _days_since(u.disabled_at) >= USER_DELETE_GRACE_DAYS


def _delete_user_records(db: Session, user_id: int) -> int:
    """Elimina definitivamente i record di effort dell'utente (Suggestion 8).

    Restituisce il numero di record eliminati.
    """
    records = db.execute(
        select(EffortEntry).where(EffortEntry.user_id == user_id)
    ).scalars().all()
    count = len(records)
    for r in records:
        db.delete(r)
    return count


@router.get("/users", response_class=HTMLResponse, name="admin_users")
async def admin_users(
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
    ok: str | None = None,
    err: str | None = None,
) -> HTMLResponse:
    """Pagina di gestione utenti (lista + form creazione).

    La tabella è di sola visualizzazione: ogni riga ha un pulsante "Modifica"
    che porta alla pagina dedicata `/admin/users/{id}/edit`.
    """
    users = db.execute(select(User).order_by(User.username)).scalars().all()
    groups = db.execute(select(Group).order_by(Group.name)).scalars().all()
    rows = [
        {
            "id": u.id,
            "username": u.username,
            "role": u.role,
            "record_count": _user_stats(db, u.id),
            "last_login": _format_last_login(u.last_login),
            "disabled": u.disabled,
            "group_name": u.group.name if u.group is not None else "",
        }
        for u in users
    ]
    admin_count = sum(1 for u in users if u.role == "admin")

    ctx = _base_context(request, admin.username, "users")
    ctx.update({
        "users": rows,
        "groups": groups,
        "admin_count": admin_count,
        "ok": ok,
        "err": err,
    })
    return templates.TemplateResponse(request=request, name="admin_users.html", context=ctx)


@router.get("/users/{user_id}/edit", response_class=HTMLResponse, name="admin_users_edit")
async def admin_users_edit(
    request: Request,
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
    ok: str | None = None,
    err: str | None = None,
) -> HTMLResponse:
    """Pagina di modifica dedicata per un singolo utente.

    Mostra i dati dell'utente e tutte le azioni di gestione (gruppo, ruolo,
    password, disabilita/abilita, eliminazione) separate dalla lista utenti.
    """
    target = db.get(User, user_id)
    if target is None:
        return RedirectResponse("/admin/users?err=Utente inesistente", status_code=303)

    groups = db.execute(select(Group).order_by(Group.name)).scalars().all()
    admin_count = db.execute(
        select(func.count()).select_from(User).where(User.role == "admin")
    ).scalar() or 0
    record_count = _user_stats(db, target.id)

    user_data = {
        "id": target.id,
        "username": target.username,
        "role": target.role,
        "disabled": target.disabled,
        "disabled_at": _format_last_login(target.disabled_at),
        "days_since_disabled": _days_since(target.disabled_at),
        "can_delete": _can_delete_user(target),
        "record_count": record_count,
        "last_login": _format_last_login(target.last_login),
        "group_id": target.group_id,
        "group_name": target.group.name if target.group is not None else "",
    }

    ctx = _base_context(request, admin.username, "users")
    ctx.update({
        "user": user_data,
        "groups": groups,
        "admin_count": admin_count,
        "is_self": target.id == admin.id,
        "ok": ok,
        "err": err,
    })
    return templates.TemplateResponse(request=request, name="admin_user_edit.html", context=ctx)


@router.post("/users/{user_id}/disable", name="admin_users_disable")
async def admin_users_disable(
    request: Request,
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> RedirectResponse:
    """Disabilita/abilita un utente (blocca il login, record intatti).

    Dopo l'azione torna alla pagina di modifica dell'utente.
    """
    if user_id == admin.id:
        logger.warning("Admin %s tenta di disabilitarsi", admin.username)
        return RedirectResponse(
            f"/admin/users/{user_id}/edit?err=Non puoi disabilitare te stesso",
            status_code=303,
        )

    target = db.get(User, user_id)
    if target is None:
        return RedirectResponse("/admin/users?err=Utente inesistente", status_code=303)

    target.disabled = not target.disabled
    # Suggestion 8: traccia il momento della disabilitazione (azzerato in riabilitazione).
    target.disabled_at = utcnow() if target.disabled else None
    db.commit()
    stato = "disabilitato" if target.disabled else "riabilitato"
    logger.info("Utente %s %s da admin %s", target.username, stato, admin.username)
    return RedirectResponse(
        f"/admin/users/{user_id}/edit?ok=Utente {stato}", status_code=303
    )


@router.post("/users/create", name="admin_users_create")
async def admin_users_create(
    request: Request,
    username: Annotated[str | None, Form()] = None,
    password: Annotated[str | None, Form()] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> RedirectResponse:
    """Crea un nuovo utente (username + password, ruolo 'user').

    Il gruppo non viene richiesto in creazione; l'admin lo assegna successivamente
    dalla pagina di modifica utente.

    Nota: usa campi Form() individuali (non Annotated[UserCreate, Form()])
    perché FastAPI non supporta modelli Form() misti ad altri Form() separati
    (stesso fix della Fase 5b). Il modello UserCreate viene costruito qui.
    """
    try:
        payload: UserCreate = UserCreate(username=username, password=password)
    except ValidationError as exc:
        logger.warning("Creazione utente non valida: %s", exc.errors())
        return RedirectResponse("/admin/users?err=Dati non validi", status_code=303)

    existing = db.execute(
        select(User).where(User.username == payload.username)
    ).scalar_one_or_none()
    if existing is not None:
        logger.warning("Tentativo di creare utente già esistente %s", payload.username)
        return RedirectResponse("/admin/users?err=Username già esistente", status_code=303)

    db.add(
        User(
            username=payload.username,
            password_hash=bcrypt.hash(payload.password),
            role="user",
            group_id=None,
        )
    )
    db.commit()
    logger.info("Utente creato da admin: %s", payload.username)
    return RedirectResponse("/admin/users?ok=Utente creato", status_code=303)


@router.post("/users/{user_id}/group", name="admin_users_group")
async def admin_users_group(
    request: Request,
    user_id: int,
    group_id: Annotated[int | None, Form()] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> RedirectResponse:
    """Assegna il gruppo di appartenenza a un utente (Fase 13a, Issue K).

    Dopo l'azione torna alla pagina di modifica dell'utente.
    """
    target = db.get(User, user_id)
    if target is None:
        return RedirectResponse("/admin/users?err=Utente inesistente", status_code=303)
    if group_id is not None:
        group = db.get(Group, group_id)
        if group is None:
            return RedirectResponse(
                f"/admin/users/{user_id}/edit?err=Gruppo inesistente", status_code=303
            )
    target.group_id = group_id
    db.commit()
    logger.info("Gruppo assegnato all'utente %s: %s", target.username, group_id)
    return RedirectResponse(
        f"/admin/users/{user_id}/edit?ok=Gruppo aggiornato", status_code=303
    )


@router.post("/users/{user_id}/password", name="admin_users_password")
async def admin_users_password(
    request: Request,
    user_id: int,
    password: Annotated[PasswordChange, Form()],
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> RedirectResponse:
    """Cambia la password di un utente.

    Dopo l'azione torna alla pagina di modifica dell'utente.
    """
    try:
        payload: PasswordChange = PasswordChange(**password.model_dump())
    except ValidationError as exc:
        logger.warning("Cambio password non valido: %s", exc.errors())
        return RedirectResponse(
            f"/admin/users/{user_id}/edit?err=Password non valida", status_code=303
        )

    target = db.get(User, user_id)
    if target is None:
        return RedirectResponse("/admin/users?err=Utente inesistente", status_code=303)
    target.password_hash = bcrypt.hash(payload.password)
    db.commit()
    logger.info("Password cambiata per %s da admin", target.username)
    return RedirectResponse(
        f"/admin/users/{user_id}/edit?ok=Password aggiornata", status_code=303
    )


@router.post("/users/{user_id}/role", name="admin_users_role")
async def admin_users_role(
    request: Request,
    user_id: int,
    role: Annotated[RoleChange, Form()],
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> RedirectResponse:
    """Cambia il ruolo di un utente (blocca l'auto-declassamento).

    Dopo l'azione torna alla pagina di modifica dell'utente.
    """
    try:
        payload: RoleChange = RoleChange(**role.model_dump())
    except ValidationError as exc:
        logger.warning("Cambio ruolo non valido: %s", exc.errors())
        return RedirectResponse(
            f"/admin/users/{user_id}/edit?err=Ruolo non valido", status_code=303
        )

    if user_id == admin.id:
        logger.warning("Admin %s tenta di auto-declassarsi", admin.username)
        return RedirectResponse(
            f"/admin/users/{user_id}/edit?err=Non puoi cambiare il tuo ruolo",
            status_code=303,
        )

    target = db.get(User, user_id)
    if target is None:
        return RedirectResponse("/admin/users?err=Utente inesistente", status_code=303)
    target.role = payload.role
    db.commit()
    logger.info("Ruolo di %s cambiato in %s", target.username, payload.role)
    return RedirectResponse(
        f"/admin/users/{user_id}/edit?ok=Ruolo aggiornato", status_code=303
    )


@router.post("/users/{user_id}/delete", name="admin_users_delete")
async def admin_users_delete(
    request: Request,
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> RedirectResponse:
    """Elimina un utente (blocca auto-eliminazione e ultimo admin).

    Dopo l'eliminazione riuscita torna alla lista utenti (l'utente non esiste
    più); negli errori bloccanti resta sulla pagina di modifica dell'utente.
    """
    if user_id == admin.id:
        logger.warning("Admin %s tenta di auto-eliminarsi", admin.username)
        return RedirectResponse(
            f"/admin/users/{user_id}/edit?err=Non puoi eliminare te stesso", status_code=303
        )

    target = db.get(User, user_id)
    if target is None:
        return RedirectResponse("/admin/users?err=Utente inesistente", status_code=303)

    if target.role == "admin":
        admin_count = db.execute(
            select(func.count()).select_from(User).where(User.role == "admin")
        ).scalar() or 0
        if admin_count <= 1:
            logger.warning("Tentativo di eliminare l'ultimo admin (%s)", target.username)
            return RedirectResponse(
                f"/admin/users/{user_id}/edit?err=Non puoi eliminare l'ultimo admin",
                status_code=303,
            )

    # Suggestion 8: finestra temporale minima dopo la disabilitazione.
    if not _can_delete_user(target):
        giorni = _days_since(target.disabled_at) or 0
        logger.warning(
            "Eliminazione utente %s bloccata: disabilitato da %d/%d giorni",
            target.username,
            giorni,
            USER_DELETE_GRACE_DAYS,
        )
        return RedirectResponse(
            f"/admin/users/{user_id}/edit?err=Eliminazione consentita dopo almeno "
            f"{USER_DELETE_GRACE_DAYS} giorni dalla disabilitazione (trascorsi {giorni})",
            status_code=303,
        )

    # Elimina definitivamente anche i record dell'utente (Suggestion 8).
    rimossi = _delete_user_records(db, target.id)
    db.delete(target)
    db.commit()
    logger.info(
        "Utente eliminato da admin: %s (record eliminati: %d)",
        target.username,
        rimossi,
    )
    return RedirectResponse(f"/admin/users?ok=Utente eliminato ({rimossi} record rimossi)", status_code=303)


# --------------------------------------------------------------------------
# Gestione lookup
# --------------------------------------------------------------------------

def _lookup_model(lookup_type: str):
    if lookup_type == "client":
        return Client
    if lookup_type == "group":
        return Group
    if lookup_type == "activity":
        return Activity
    raise ValueError(f"Tipo lookup non valido: {lookup_type}")


def _lookup_label(lookup_type: str) -> str:
    return {
        "client": "Clienti",
        "group": "Gruppi",
        "activity": "Attività",
    }.get(lookup_type, lookup_type)


@router.get("/lookup", response_class=HTMLResponse, name="admin_lookup")
async def admin_lookup(
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
    ok: str | None = None,
    err: str | None = None,
) -> HTMLResponse:
    """Pagina di gestione lookup: clienti, gruppi, attività."""
    clients = db.execute(select(Client).order_by(Client.name)).scalars().all()
    groups = db.execute(select(Group).order_by(Group.name)).scalars().all()
    activities = db.execute(select(Activity).order_by(Activity.name)).scalars().all()

    # Conta i record associati a ciascun lookup (per bloccare l'eliminazione).
    used_client_ids = set(
        db.execute(select(EffortEntry.client_id).distinct()).scalars().all()
    )
    used_group_ids = set(
        db.execute(select(EffortEntry.group_id).distinct()).scalars().all()
    )
    used_activity_ids = set(
        db.execute(select(EffortEntry.activity_id).distinct()).scalars().all()
    )

    ctx = _base_context(request, admin.username, "lookup")
    ctx.update({
        "clients": clients,
        "groups": groups,
        "activities": activities,
        "used_client_ids": used_client_ids,
        "used_group_ids": used_group_ids,
        "used_activity_ids": used_activity_ids,
        "ok": ok,
        "err": err,
    })
    return templates.TemplateResponse(request=request, name="admin_lookup.html", context=ctx)


@router.post("/lookup/create", name="admin_lookup_create")
async def admin_lookup_create(
    request: Request,
    lookup: Annotated[LookupCreate, Form()],
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> RedirectResponse:
    """Aggiunge una voce lookup."""
    try:
        payload: LookupCreate = LookupCreate(**lookup.model_dump())
    except ValidationError as exc:
        logger.warning("Creazione lookup non valida: %s", exc.errors())
        return RedirectResponse("/admin/lookup?err=Dati non validi", status_code=303)

    model = _lookup_model(payload.type)
    existing = db.execute(
        select(model).where(model.name == payload.name)
    ).scalar_one_or_none()
    if existing is not None:
        return RedirectResponse("/admin/lookup?err=Nome già esistente", status_code=303)

    db.add(model(name=payload.name))
    db.commit()
    logger.info("Lookup %s creato: %s", payload.type, payload.name)
    return RedirectResponse("/admin/lookup?ok=Elemento aggiunto", status_code=303)


@router.post("/lookup/{lookup_id}/edit", name="admin_lookup_edit")
async def admin_lookup_edit(
    request: Request,
    lookup_id: int,
    lookup_type: Annotated[str, Form()],
    name: Annotated[str, Form()],
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> RedirectResponse:
    """Modifica il nome di una voce lookup."""
    try:
        payload: LookupCreate = LookupCreate(type=lookup_type, name=name)
    except ValidationError as exc:
        logger.warning("Modifica lookup non valida: %s", exc.errors())
        return RedirectResponse("/admin/lookup?err=Nome non valido", status_code=303)

    model = _lookup_model(payload.type)
    target = db.get(model, lookup_id)
    if target is None:
        return RedirectResponse("/admin/lookup?err=Elemento inesistente", status_code=303)
    target.name = payload.name
    db.commit()
    logger.info("Lookup %s id=%s rinominato in %s", payload.type, lookup_id, payload.name)
    return RedirectResponse("/admin/lookup?ok=Elemento aggiornato", status_code=303)


@router.post("/lookup/{lookup_id}/delete", name="admin_lookup_delete")
async def admin_lookup_delete(
    request: Request,
    lookup_id: int,
    lookup_type: Annotated[str, Form()],
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> RedirectResponse:
    """Elimina una voce lookup (bloccato se ha record associati)."""
    try:
        model = _lookup_model(lookup_type)
    except ValueError as exc:
        return RedirectResponse("/admin/lookup?err=Tipo non valido", status_code=303)

    target = db.get(model, lookup_id)
    if target is None:
        return RedirectResponse("/admin/lookup?err=Elemento inesistente", status_code=303)

    # Colonna FK che collega il lookup a effort_entries.
    fk_col = {
        Client: EffortEntry.client_id,
        Group: EffortEntry.group_id,
        Activity: EffortEntry.activity_id,
    }[model]

    associated = db.execute(
        select(func.count()).select_from(EffortEntry).where(fk_col == lookup_id)
    ).scalar() or 0
    if associated > 0:
        logger.warning(
            "Eliminazione lookup %s id=%s bloccata: %d record associati",
            lookup_type,
            lookup_id,
            associated,
        )
        return RedirectResponse("/admin/lookup?err=Elemento con record associati", status_code=303)

    db.delete(target)
    db.commit()
    logger.info("Lookup %s id=%s eliminato", lookup_type, lookup_id)
    return RedirectResponse("/admin/lookup?ok=Elemento eliminato", status_code=303)