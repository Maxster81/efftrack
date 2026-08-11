"""Router amministrativo.

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
import os
from datetime import date, datetime, timedelta
from typing import Annotated

from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.config import (
    APP_NAME,
    APP_VERSION,
    AUTH_ENABLED,
    DATABASE_URL,
    TEMPLATES_DIR,
    USER_DELETE_GRACE_DAYS,
)
from app.core.password import generate_password, hash_password
from app.core.permissions import require_admin
from app.core.seed import SENTINEL_NAME
from app.db import get_db
from app.models import Activity, Client, EffortEntry, Group, User
from app.models.effort_entry import utcnow
from app.routers.web import _resolve_month
from app.schemas.effort import LookupCreate, PasswordChange, RoleChange, UserCreate
from fastapi.templating import Jinja2Templates

logger: logging.Logger = logging.getLogger(__name__)

templates: Jinja2Templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

router: APIRouter = APIRouter(prefix="/admin", tags=["admin"])

# Nomi dei mesi in italiano.
_MESI_ITALIANI = [
    "", "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
    "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre",
]


def _sidebar_items() -> list[dict[str, str]]:
    """Voci della sidebar dell'area admin."""
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
        "phase": "Pannello Admin",
        "current_username": current_username,
        "auth_enabled": AUTH_ENABLED,
        "is_admin": True,
        "sidebar_items": _sidebar_items(),
        "active": active,
    }


def _db_size_mb() -> str:
    """Dimensione del file SQLite in MB (fallback a '—' se non è un file)."""
    if not DATABASE_URL.startswith("sqlite:///"):
        return "—"
    db_path = DATABASE_URL.replace("sqlite:///", "", 1)
    try:
        size = os.path.getsize(db_path)
        return f"{size / (1024 * 1024):.1f} MB"
    except OSError:
        return "—"


def _month_bounds() -> tuple[date, date]:
    """Estremi (primo e ultimo giorno) del mese corrente."""
    today = date.today()
    start = today.replace(day=1)
    next_month = (start.replace(day=28) + timedelta(days=4)).replace(day=1)
    return start, next_month - timedelta(days=1)


def _inactive_users(db: Session, days: int = 7) -> list[tuple[str, int | None]]:
    """Utenti non disabilitati che non registrano effort da almeno `days` giorni.

    Restituisce coppie (username, giorni_dall_ultimo_record) ordinate per
    inattività decrescente. Gli utenti senza alcun record sono considerati
    inattivi con giorni = None.
    """
    cutoff = date.today() - timedelta(days=days)
    users = db.execute(select(User)).scalars().all()
    last_date_expr = (
        select(func.max(EffortEntry.work_date))
        .where(EffortEntry.user_id == User.id)
        .scalar_subquery()
    )
    rows = []
    for u in users:
        if u.disabled:
            continue
        last = db.execute(
            select(last_date_expr).where(User.id == u.id)
        ).scalar()
        if last is None:
            rows.append((u.username, None))
        elif last < cutoff:
            rows.append((u.username, (date.today() - last).days))
    rows.sort(key=lambda item: (item[1] is None, item[1] if item[1] is not None else 10**9), reverse=True)
    return rows


@router.get("", response_class=HTMLResponse, name="admin_dashboard")
async def admin_dashboard(
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> HTMLResponse:
    """Dashboard admin con KPI e metriche di sistema."""
    today = date.today()
    m_start, m_end = _month_bounds()

    # --- KPI base -----------------------------------------------------------
    total_users = db.execute(select(func.count()).select_from(User)).scalar() or 0
    active_users = db.execute(
        select(func.count()).select_from(User).where(User.disabled.is_(False))
    ).scalar() or 0
    disabled_users = total_users - active_users
    total_records = db.execute(
        select(func.count()).select_from(EffortEntry)
    ).scalar() or 0

    hours_month = db.execute(
        select(func.coalesce(func.sum(EffortEntry.hours_spent), 0)).where(
            EffortEntry.work_date >= m_start,
            EffortEntry.work_date <= m_end,
        )
    ).scalar() or 0
    records_today = db.execute(
        select(func.count()).select_from(EffortEntry).where(
            EffortEntry.work_date == today
        )
    ).scalar() or 0

    # --- Distribuzione per gruppo (utenti + ore del mese) ------------------
    group_rows = []
    for g in db.execute(select(Group).order_by(Group.name)).scalars().all():
        user_count = db.execute(
            select(func.count()).select_from(User).where(
                User.group_id == g.id,
                User.disabled.is_(False),
            )
        ).scalar() or 0
        hours = db.execute(
            select(func.coalesce(func.sum(EffortEntry.hours_spent), 0)).where(
                EffortEntry.group_id == g.id,
                EffortEntry.work_date >= m_start,
                EffortEntry.work_date <= m_end,
            )
        ).scalar() or 0
        group_rows.append({"name": g.name, "users": user_count, "hours": float(hours)})

    # --- Ultima attività ------------------------------------------------------
    recent_records = (
        db.execute(
            select(EffortEntry)
            .options(
                selectinload(EffortEntry.client),
                selectinload(EffortEntry.group),
                selectinload(EffortEntry.activity),
                selectinload(EffortEntry.user),
            )
            .order_by(EffortEntry.work_date.desc(), EffortEntry.created_at.desc())
            .limit(20)
        )
        .scalars()
        .all()
    )
    last_record = recent_records[0] if recent_records else None

    ctx = _base_context(request, admin.username, "dashboard")
    ctx.update({
        "kpi": {
            "total_users": total_users,
            "active_users": active_users,
            "disabled_users": disabled_users,
            "total_records": total_records,
            "hours_month": hours_month,
            "records_today": records_today,
        },
        "group_stats": group_rows,
        "inactive_users": _inactive_users(db, days=7),
        "recent_records": recent_records,
        "last_record": last_record,
        "month_label": f"{_MESI_ITALIANI[today.month]} {today.year}",
        "db_size": _db_size_mb(),
    })
    return templates.TemplateResponse(
        request=request,
        name="admin_dashboard.html",
        context=ctx,
    )


@router.get("/records", response_class=HTMLResponse, name="admin_records")
async def admin_records(
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
    month: str | None = None,
    year: str | None = None,
    month_num: str | None = None,
) -> HTMLResponse:
    """Tabella di tutti i record del sistema (no form, con filtro anno/mese)."""
    filter_month = _resolve_month(year, month_num, month)

    # Anni distinti presenti (ordinati desc).
    year_stmt = (
        select(func.strftime("%Y", EffortEntry.work_date).label("year"))
        .distinct()
        .order_by(func.strftime("%Y", EffortEntry.work_date).desc())
    )
    year_options = db.execute(year_stmt).scalars().all()

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
    if filter_month:
        stmt = stmt.where(func.strftime("%Y-%m", EffortEntry.work_date) == filter_month)
    records = db.execute(stmt).scalars().all()

    selected_year: str = ""
    selected_month_num: str = ""
    if filter_month and len(filter_month) == 7:
        y, m = filter_month.split("-")
        selected_year = y
        selected_month_num = m

    ctx = _base_context(request, admin.username, "records")
    ctx.update({
        "records": records,
        "year_options": year_options,
        "month_options": _MESI_ITALIANI,
        "selected_year": selected_year,
        "selected_month_num": selected_month_num,
    })
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
    year: str | None = None,
    month_num: str | None = None,
) -> StreamingResponse:
    """Esporta in CSV tutti i record del sistema (solo admin)."""
    filter_month = _resolve_month(year, month_num, month)

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
    if filter_month:
        stmt = stmt.where(func.strftime("%Y-%m", EffortEntry.work_date) == filter_month)
    records = db.execute(stmt).scalars().all()

    filename = f"effort_admin_{filter_month or 'tutti'}.csv"
    logger.info("Export CSV admin (record=%d, mese=%s)", len(records), filter_month or "tutti")
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
    """Elimina definitivamente i record di effort dell'utente.

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
    form_ok: str | None = None,
    form_err: str | None = None,
) -> HTMLResponse:
    """Pagina di gestione utenti (lista + form creazione).

    La tabella è di sola visualizzazione: ogni riga ha un pulsante "Modifica"
    che porta alla pagina dedicata `/admin/users/{id}/edit`.
    `ok`/`err` alimentano il banner nella card "Utenti" (operazioni sulla lista);
    `form_ok`/`form_err` alimentano il banner nella card "Nuovo utente" (creazione).
    """
    users = db.execute(select(User).order_by(User.username)).scalars().all()
    groups = db.execute(select(Group).order_by(Group.name)).scalars().all()
    rows = [
        {
            "id": u.id,
            "username": u.username,
            "first_name": u.first_name or "",
            "last_name": u.last_name or "",
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
        "form_ok": form_ok,
        "form_err": form_err,
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
        "first_name": target.first_name or "",
        "last_name": target.last_name or "",
        "email": target.email or "",
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
    # Traccia il momento della disabilitazione (azzerato in riabilitazione).
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
    first_name: Annotated[str | None, Form()] = None,
    last_name: Annotated[str | None, Form()] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> RedirectResponse:
    """Crea un nuovo utente (username email + nome/cognome, ruolo 'user').

    La password viene modificata automaticamente in modo robusto e mostrata
    UNA SOLA volta nel banner di conferma dopo il redirect. Il gruppo non
    viene richiesto in creazione; l'admin lo assegna successivamente dalla
    pagina di modifica utente.

    Nota: usa campi Form() individuali (non Annotated[UserCreate, Form()])
    perché FastAPI non supporta modelli Form() misti ad altri Form() separati.
    Il modello UserCreate viene costruito qui.
    """
    try:
        payload: UserCreate = UserCreate(
            username=username, first_name=first_name, last_name=last_name
        )
    except ValidationError as exc:
        logger.warning("Creazione utente non valida: %s", exc.errors())
        return RedirectResponse("/admin/users?form_err=Dati non validi", status_code=303)

    existing = db.execute(
        select(User).where(User.username == payload.username)
    ).scalar_one_or_none()
    if existing is not None:
        logger.warning("Tentativo di creare utente già esistente %s", payload.username)
        return RedirectResponse("/admin/users?form_err=Username già esistente", status_code=303)

    # Genera una password robusta e la mostra una sola volta nel banner.
    generated_password = generate_password()
    db.add(
        User(
            username=payload.username,
            password_hash=hash_password(generated_password),
            first_name=payload.first_name,
            last_name=payload.last_name,
            email=payload.username,
            role="user",
            group_id=None,
            # La password generata è temporanea: al primo login l'utente è
            # obbligato a cambiarla (password_change_required).
            password_change_required=True,
        )
    )
    db.commit()
    logger.info("Utente creato da admin: %s", payload.username)
    # URL-encode del messaggio: la password generata contiene caratteri
    # speciali (es. &, =, ?) che, non encodati, romperebbero il parametro
    # `form_ok` della query string. FastAPI decodifica il parametro e il
    # banner mostra la password originale. `form_ok`/`form_err` alimentano
    # il banner nella card "Nuovo utente", distinto da `ok`/`err` della lista.
    ok_msg = f"Utente creato. Password temporanea: {generated_password}"
    return RedirectResponse(
        f"/admin/users?{urlencode({'form_ok': ok_msg})}",
        status_code=303,
    )


@router.post("/users/{user_id}/profile", name="admin_users_profile")
async def admin_users_profile(
    request: Request,
    user_id: int,
    username: Annotated[str | None, Form()] = None,
    first_name: Annotated[str | None, Form()] = None,
    last_name: Annotated[str | None, Form()] = None,
    email: Annotated[str | None, Form()] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> RedirectResponse:
    """Aggiorna i dati anagrafici di un utente (username, nome, cognome, email).

    Dopo l'azione torna alla pagina di modifica dell'utente.
    """
    try:
        payload: UserCreate = UserCreate(
            username=username, first_name=first_name, last_name=last_name
        )
    except ValidationError as exc:
        logger.warning("Dati anagrafici non validi per utente id=%s", user_id)
        return RedirectResponse(
            f"/admin/users/{user_id}/edit?err=Dati non validi", status_code=303
        )

    target = db.get(User, user_id)
    if target is None:
        return RedirectResponse("/admin/users?err=Utente inesistente", status_code=303)

    # Eventuale email distinta dall'username (se non fornita, usa l'username).
    stripped_email = (email or "").strip()
    new_email = stripped_email if stripped_email else payload.username

    # Controllo duplicazione username (escluso l'utente stesso).
    existing = db.execute(
        select(User).where(User.username == payload.username, User.id != user_id)
    ).scalar_one_or_none()
    if existing is not None:
        logger.warning("Tentativo di usare username già esistente %s", payload.username)
        return RedirectResponse(
            f"/admin/users/{user_id}/edit?err=Username già esistente", status_code=303
        )

    target.username = payload.username
    target.first_name = payload.first_name
    target.last_name = payload.last_name
    target.email = new_email
    db.commit()
    logger.info("Dati anagrafici aggiornati per %s da admin", target.username)
    return RedirectResponse(
        f"/admin/users/{user_id}/edit?ok=Dati anagrafici aggiornati", status_code=303
    )


@router.post("/users/{user_id}/group", name="admin_users_group")
async def admin_users_group(
    request: Request,
    user_id: int,
    group_id: Annotated[int | None, Form()] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> RedirectResponse:
    """Assegna il gruppo di appartenenza a un utente.

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
        logger.warning("Cambio password non valido per utente id=%s", user_id)
        return RedirectResponse(
            f"/admin/users/{user_id}/edit?err=Password non valida", status_code=303
        )

    target = db.get(User, user_id)
    if target is None:
        return RedirectResponse("/admin/users?err=Utente inesistente", status_code=303)
    target.password_hash = hash_password(payload.password)
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

    # Finestra temporale minima dopo la disabilitazione.
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

    # Elimina definitivamente anche i record dell'utente.
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

    # La voce sentinella "NON LAVORATO" (S6) non può essere creata via UI:
    # è gestita esclusivamente dal seed. Evita collisioni col meccanismo giorni
    # non lavorati.
    if payload.name.upper() == SENTINEL_NAME:
        logger.warning("Creazione lookup '%s' bloccata (sentinella)", payload.name)
        return RedirectResponse(
            "/admin/lookup?err=Nome riservato", status_code=303
        )

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

    # La voce sentinella "NON LAVORATO" non è rinominabile: è un meccanismo
    # interno usato per i giorni non lavorati (S6). Rinomarla romperebbe
    # l'allineamento dell'app con il nome sentinella.
    if target.name.upper() == SENTINEL_NAME:
        logger.warning("Rinomina lookup sentinella '%s' bloccata", target.name)
        return RedirectResponse(
            "/admin/lookup?err=Elemento sentinella non modificabile", status_code=303
        )

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

    # La voce sentinella "NON LAVORATO" non è eliminabile: è un meccanismo
    # interno (S6). Protezione esplicita, oltre al blocco per record associati.
    if target.name.upper() == SENTINEL_NAME:
        logger.warning("Eliminazione lookup sentinella '%s' bloccata", target.name)
        return RedirectResponse(
            "/admin/lookup?err=Elemento sentinella non eliminabile", status_code=303
        )

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