"""Router web dell'applicazione Effort Tracking.

Espone le pagine HTML renderizzate server-side con Jinja2 e gli endpoint
di base (indice, health check). Dalla Fase 10 le route business sono
protette: se l'autenticazione è attiva e non c'è una sessione valida,
l'utente viene rediretto al login.

Fase 11: segregazione dati per utente. Ogni utente normale vede, crea,
modifica ed esporta solo i propri record; l'admin (ruolo "admin") vede
tutti i record come supervisore. `user_id` viene valorizzato su ogni
nuovo record con l'utente della sessione.
"""
from __future__ import annotations

import csv
import io
import logging
from datetime import date, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, StreamingResponse
from pydantic import ValidationError
from sqlalchemy import Select, func, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, selectinload
from fastapi.templating import Jinja2Templates

from app.config import APP_NAME, APP_VERSION, AUTH_ENABLED, TEMPLATES_DIR
from app.core.permissions import is_admin, is_manager
from app.db import get_db
from app.dependencies import get_current_user
from app.models import Activity, Client, EffortEntry, Group, User
from app.schemas.effort import EffortEntryCreate

logger: logging.Logger = logging.getLogger(__name__)

# Template engine condiviso dal router web.
templates: Jinja2Templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


router: APIRouter = APIRouter(tags=["web"])

# Nomi dei mesi in italiano (indice 0 vuoto, 1..12).
_MESI_ITALIANI = [
    "", "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
    "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre",
]

# Header del CSV di export (Fase 8), coerente con le colonne della tabella.
_CSV_HEADER = [
    "Data",
    "Cliente",
    "Gruppo",
    "Attività",
    "Utente",
    "Ore",
    "Note",
    "Descrizione attività",
]


def _require_auth(user: User | None) -> RedirectResponse | None:
    """Se l'auth è attiva e manca l'utente, restituisce il redirect al login."""
    if AUTH_ENABLED and user is None:
        return RedirectResponse("/login", status_code=303)
    return None


def _filter_by_user(stmt: Select, user: User) -> Select:
    """Filtra una query sugli effort in base al ruolo.

    L'admin vede tutti i record; un utente normale solo i propri.
    """
    if is_admin(user):
        return stmt
    return stmt.where(EffortEntry.user_id == user.id)


def _with_month(base_url: str, month: str | None) -> str:
    """Aggiunge il parametro month a un URL se presente (Issue 1: filtri)."""
    if month and month != "None":  # "None" (stringa) = mese non valido
        separator: str = "&" if "?" in base_url else "?"
        return f"{base_url}{separator}month={month}"
    return base_url


def _sidebar_items(user: User) -> list[dict[str, str]]:
    """Voci della sidebar in base al ruolo dell'utente loggato (Fasi 12b/12c/12d).

    - USER: solo "Registrazioni".
    - MANAGER: "Registrazioni" + "Gruppo" (vista gruppo, Fase 12c).
    - ADMIN: Dashboard + Registrazioni + Gestione Utenti + Gestione Lookup (Fase 12d).
      L'admin atterra su `/admin` e gestisce tutto dall'area admin.
    """
    if is_admin(user):
        return [
            {"label": "Dashboard", "href": "/admin"},
            {"label": "Registrazioni", "href": "/admin/records"},
            {"label": "Gestione Utenti", "href": "/admin/users"},
            {"label": "Gestione Lookup", "href": "/admin/lookup"},
        ]
    items: list[dict[str, str]] = [
        {"label": "Registrazioni", "href": "/"},
    ]
    if is_manager(user):
        items.append({"label": "Gruppo", "href": "/group"})
    return items


@router.get("/", response_class=HTMLResponse, name="index")
async def index(
    request: Request,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
    success: int | None = None,
    error: str | None = None,
    month: str | None = None,
) -> HTMLResponse:
    """Pagina principale: form di inserimento + tabella elenco (protetta)."""
    redirect = _require_auth(user)
    if redirect is not None:
        return redirect
    assert user is not None  # con auth attiva, dopo _require_auth l'utente c'è.

    # Fase 12d: l'admin atterra sulla dashboard /admin, non sulla pagina
    # di registrazione (che non può usare: niente card form, solo consultazione).
    if is_admin(user):
        return RedirectResponse("/admin", status_code=303)

    clients = db.execute(select(Client).order_by(Client.name)).scalars().all()
    groups = db.execute(select(Group).order_by(Group.name)).scalars().all()
    activities = db.execute(select(Activity).order_by(Activity.name)).scalars().all()

    # Mesi distinti limitati ai record visibili all'utente (Fase 11).
    month_stmt = (
        select(func.strftime("%Y-%m", EffortEntry.work_date).label("month"))
        .distinct()
        .order_by(func.strftime("%Y-%m", EffortEntry.work_date).desc())
    )
    month_stmt = _filter_by_user(month_stmt, user)
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
    stmt = _filter_by_user(stmt, user)
    if month:
        stmt = stmt.where(func.strftime("%Y-%m", EffortEntry.work_date) == month)
    records = db.execute(stmt).scalars().all()

    success_message: str | None = None
    if success == 1:
        success_message = "Record salvato correttamente."
    elif success == 2:
        success_message = "Registrazione aggiornata correttamente."
    elif success == 3:
        success_message = "Registrazione eliminata correttamente."

    current_username: str = user.username

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "app_name": APP_NAME,
            "app_version": APP_VERSION,
            "phase": "Fase 11 — Multiutente e segregazione",
            "clients": clients,
            "groups": groups,
            "activities": activities,
            "records": records,
            "month_options": month_options,
            "selected_month": month,
            "today": date.today().isoformat(),
            "success_message": success_message,
            "error": error,
            "current_username": current_username,
            "auth_enabled": AUTH_ENABLED,
            "is_admin": is_admin(user),
            "sidebar_items": _sidebar_items(user),
        },
    )


@router.post("/", response_class=HTMLResponse, name="save_entry")
async def save_entry(
    request: Request,
    user: Annotated[str | None, Form()] = None,
    date: Annotated[date | None, Form()] = None,
    client_id: Annotated[int | None, Form()] = None,
    group_id: Annotated[int | None, Form()] = None,
    activity_id: Annotated[int | None, Form()] = None,
    hours: Annotated[float | None, Form()] = None,
    notes: Annotated[str | None, Form()] = None,
    description: Annotated[str | None, Form()] = None,
    action: Annotated[str, Form()] = "single",
    record_id: Annotated[int | None, Form()] = None,
    month: Annotated[str | None, Form()] = None,
    current_user: User | None = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    """Salva o aggiorna un record di effort (protetta).

    Con auth attiva, il campo User viene forzato lato server allo username
    della sessione, indipendentemente da quanto inviato dal browser.
    `month` preserva il filtro mese nel redirect (Issue-Suggestion.md Issue 1).
    Fase 11: `user_id` viene valorizzato con l'utente della sessione.
    """
    redirect = _require_auth(current_user)
    if redirect is not None:
        return redirect
    assert current_user is not None

    # Con auth attiva, rispetta sempre l'utente della sessione (il campo
    # User è readonly lato client, ma qui se ne garantisce l'integrità).
    if AUTH_ENABLED:
        user = current_user.username

    # Eliminazione definitiva: richiede solo `record_id`.
    if action == "delete":
        return _delete_entry(record_id, db, current_user, month)

    try:
        payload = EffortEntryCreate(
            user=user,
            date=date,
            client_id=client_id,
            group_id=group_id,
            activity_id=activity_id,
            hours=hours,
            notes=notes,
            description=description,
        )
    except ValidationError as exc:
        logger.warning("Validazione fallita nel form: %s", exc.errors())
        return RedirectResponse(_with_month("/?error=validazione", month), status_code=303)

    activity = db.execute(
        select(Activity).where(Activity.id == payload.activity_id)
    ).scalar_one_or_none()

    if activity is not None and activity.requires_description and not payload.description:
        logger.warning("Descrizione mancante per attività che la richiede")
        return RedirectResponse(_with_month("/?error=descrizione", month), status_code=303)

    if action == "week" and record_id is not None:
        return RedirectResponse(_with_month("/?error=validazione", month), status_code=303)

    if action == "week":
        return _save_week(payload, db, current_user, month)

    return _save_single(payload, db, current_user, record_id=record_id, month=month)


def _delete_entry(
    record_id: int | None,
    db: Session,
    current_user: User,
    month: str | None = None,
) -> RedirectResponse:
    """Elimina definitivamente un record di effort dal database.

    Fase 11: ogni utente può eliminare SOLO i propri record. Nessuna
    eccezione per admin/manager — la modifica o cancellazione di record
    altrui non è mai consentita (regola aziendale: nessuno tocca i dati
    degli altri, nemmeno con ruolo di supervisione).
    """
    if record_id is None:
        logger.warning("Eliminazione senza record_id")
        return RedirectResponse(_with_month("/?error=validazione", month), status_code=303)

    entry = db.get(EffortEntry, record_id)
    if entry is None:
        logger.warning("Tentativo di eliminazione record inesistente id=%s", record_id)
        return RedirectResponse(_with_month("/?error=validazione", month), status_code=303)

    if entry.user_id != current_user.id:
        logger.warning(
            "Utente %s tenta di eliminare record altrui id=%s",
            current_user.username,
            record_id,
        )
        return RedirectResponse(_with_month("/?error=validazione", month), status_code=303)

    db.delete(entry)
    db.commit()
    logger.info("Record eliminato id=%s", record_id)
    return RedirectResponse(_with_month("/?success=3", month), status_code=303)


def _save_single(
    payload: EffortEntryCreate,
    db: Session,
    current_user: User,
    record_id: int | None = None,
    month: str | None = None,
) -> RedirectResponse:
    """Crea un nuovo record oppure aggiorna quello indicato da `record_id`.

    Fase 11: il nuovo record viene associato all'utente corrente; su update
    ogni utente può modificare SOLO i propri record (nessuna eccezione per
    admin/manager — regola aziendale).
    """
    if record_id is not None:
        entry = db.get(EffortEntry, record_id)
        if entry is None:
            logger.warning("Update di record inesistente id=%s", record_id)
            return RedirectResponse(_with_month("/?error=validazione", month), status_code=303)
        # Fase 11: ogni utente può aggiornare SOLO i propri record. Nessuna
        # eccezione per admin/manager (regola aziendale).
        if entry.user_id != current_user.id:
            logger.warning(
                "Utente %s tenta di aggiornare record altrui id=%s",
                current_user.username,
                record_id,
            )
            return RedirectResponse(_with_month("/?error=validazione", month), status_code=303)
        # Su update il proprietario del record non cambia (è sempre l'utente
        # corrente, già verificato sopra).
        entry.client_id = payload.client_id
        entry.group_id = payload.group_id
        entry.activity_id = payload.activity_id
        entry.work_date = payload.date
        entry.hours_spent = payload.hours
        entry.notes = payload.notes
        entry.description = payload.description
        db.commit()
        logger.info("Record aggiornato id=%s data=%s ore=%s", record_id, payload.date, payload.hours)
        return RedirectResponse(_with_month("/?success=2", month), status_code=303)

    entry = EffortEntry(
        user_id=current_user.id,
        client_id=payload.client_id,
        group_id=payload.group_id,
        activity_id=payload.activity_id,
        work_date=payload.date,
        hours_spent=payload.hours,
        notes=payload.notes,
        description=payload.description,
    )
    db.add(entry)
    db.commit()
    logger.info("Record creato id=%s data=%s ore=%s", entry.id, payload.date, payload.hours)
    return RedirectResponse(_with_month("/?success=1", month), status_code=303)


def _save_week(
    payload: EffortEntryCreate,
    db: Session,
    current_user: User,
    month: str | None = None,
) -> RedirectResponse:
    """Copia il form su tutti i giorni feriali della settimana della data.

    Fase 11: tutti i record creati vengono associati all'utente corrente.
    """
    monday = payload.date - timedelta(days=payload.date.weekday())
    for offset in range(5):  # lun, mar, mer, gio, ven
        db.add(
            EffortEntry(
                user_id=current_user.id,
                client_id=payload.client_id,
                group_id=payload.group_id,
                activity_id=payload.activity_id,
                work_date=monday + timedelta(days=offset),
                hours_spent=payload.hours,
                notes=payload.notes,
                description=payload.description,
            )
        )
    db.commit()
    logger.info("Copia settimanale creata (settimana di %s)", payload.date.isoformat())
    return RedirectResponse(_with_month("/?success=1", month), status_code=303)


@router.get("/export", response_class=StreamingResponse, name="export_csv")
async def export_csv(
    request: Request,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
    month: str | None = None,
) -> StreamingResponse:
    """Esporta i record di effort in formato CSV (protetta, segregata)."""
    redirect = _require_auth(user)
    if redirect is not None:
        return redirect
    assert user is not None

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
    stmt = _filter_by_user(stmt, user)
    if month:
        stmt = stmt.where(func.strftime("%Y-%m", EffortEntry.work_date) == month)
    records = db.execute(stmt).scalars().all()

    filename = f"effort_{month}.csv" if month else "effort_tutti.csv"
    logger.info("Export CSV generato (record=%d, mese=%s)", len(records), month or "tutti")
    return StreamingResponse(
        iter([_build_csv(records)]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _build_csv(records: list[EffortEntry]) -> str:
    """Costruisce il contenuto CSV (con BOM UTF-8) dai record di effort.

    Fase 11: la colonna Utente mostra lo username reale dal JOIN su users;
    per i record senza proprietario (legacy) mostra una stringa vuota.
    """
    buffer = io.StringIO()
    buffer.write("\ufeff")  # BOM UTF-8 per compatibilità Excel/Windows.
    writer = csv.writer(buffer)
    writer.writerow(_CSV_HEADER)
    for record in records:
        writer.writerow(
            [
                record.work_date.strftime("%d/%m/%Y"),
                record.client.name,
                record.group.name,
                record.activity.name,
                record.user.username if record.user is not None else "",
                record.hours_spent,
                record.notes or "",
                record.description or "",
            ]
        )
    return buffer.getvalue()


def _is_manager_view(user: User | None) -> bool:
    """True se l'utente è un manager (con un gruppo da gestire)."""
    return user is not None and is_manager(user) and user.group_id is not None


def _records_in_group_statement(db: Session, group_id: int) -> Select:
    """Restituisce lo statement SQL dei record di tutti gli utenti del gruppo.

    Fase 12c: la vista gruppo del manager mostra i record di tutti gli utenti
    che hanno `group_id` uguale a quello del manager.
    """
    user_ids = db.execute(select(User.id).where(User.group_id == group_id)).scalars().all()
    stmt: Select = (
        select(EffortEntry)
        .options(
            selectinload(EffortEntry.client),
            selectinload(EffortEntry.group),
            selectinload(EffortEntry.activity),
            selectinload(EffortEntry.user),
        )
        .order_by(EffortEntry.work_date.desc())
    )
    if user_ids:
        stmt = stmt.where(EffortEntry.user_id.in_(user_ids))
    else:
        # Nessun membro nel gruppo: nessun record visibile.
        stmt = stmt.where(False)
    return stmt


def _records_in_group(db: Session, group_id: int, month: str | None) -> list[EffortEntry]:
    """Restituisce i record del gruppo indicato, opzionalmente filtrati per mese."""
    stmt = _records_in_group_statement(db, group_id)
    if month:
        stmt = stmt.where(func.strftime("%Y-%m", EffortEntry.work_date) == month)
    return db.execute(stmt).scalars().all()


def _month_options_in_group(db: Session, group_id: int) -> list[tuple[str, str]]:
    """Calcola le opzioni mese (YYYY-MM, label italiana) per i record del gruppo."""
    month_stmt = (
        select(func.strftime("%Y-%m", EffortEntry.work_date).label("month"))
        .distinct()
        .order_by(func.strftime("%Y-%m", EffortEntry.work_date).desc())
        .where(
            EffortEntry.user_id.in_(
                select(User.id).where(User.group_id == group_id)
            )
        )
    )
    month_rows = db.execute(month_stmt).scalars().all()
    return [
        (m, f"{_MESI_ITALIANI[int(m.split('-')[1])]} {m.split('-')[0]}")
        for m in month_rows
    ]


@router.get("/group", response_class=HTMLResponse, name="group_view")
async def group_view(
    request: Request,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
    month: str | None = None,
) -> HTMLResponse:
    """Pagina del gruppo per il manager: solo visualizzazione/esportazione (Fase 12c).

    Il manager vede i record di tutti gli utenti del gruppo che gestisce,
    con filtro mese/anno. Non c'è il form di inserimento: la vista è read-only.
    """
    redirect = _require_auth(user)
    if redirect is not None:
        return redirect
    assert user is not None
    if not _is_manager_view(user):
        logger.warning("Accesso negato a /group per utente %s (ruolo=%s)", user.username, user.role)
        return RedirectResponse("/", status_code=303)

    group = db.get(Group, user.group_id)
    records = _records_in_group(db, user.group_id, month)
    month_options = _month_options_in_group(db, user.group_id)

    return templates.TemplateResponse(
        request=request,
        name="group.html",
        context={
            "app_name": APP_NAME,
            "app_version": APP_VERSION,
            "phase": "Fase 12c — Vista gruppo (manager)",
            "group_name": group.name if group else "Gruppo",
            "records": records,
            "month_options": month_options,
            "selected_month": month,
            "current_username": user.username,
            "auth_enabled": AUTH_ENABLED,
            "is_admin": is_admin(user),
            "sidebar_items": _sidebar_items(user),
        },
    )


@router.get("/group/export", response_class=StreamingResponse, name="group_export_csv")
async def group_export_csv(
    request: Request,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
    month: str | None = None,
) -> StreamingResponse:
    """Esporta in CSV i record del gruppo gestito dal manager (Fase 12c)."""
    redirect = _require_auth(user)
    if redirect is not None:
        return redirect
    assert user is not None
    if not _is_manager_view(user):
        logger.warning("Export negato per utente %s (ruolo=%s)", user.username, user.role)
        return RedirectResponse("/", status_code=303)

    group = db.get(Group, user.group_id)
    stmt = _records_in_group_statement(db, user.group_id)
    if month:
        stmt = stmt.where(func.strftime("%Y-%m", EffortEntry.work_date) == month)
    records = db.execute(stmt.order_by(EffortEntry.work_date.asc())).scalars().all()

    filename = f"effort_{group.name if group else 'gruppo'}_{month or 'tutti'}.csv"
    logger.info("Export CSV gruppo generato (record=%d, mese=%s)", len(records), month or "tutti")
    return StreamingResponse(
        iter([_build_csv(records)]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/health", name="health")
async def health() -> JSONResponse:
    """Health check: stato applicazione + check base della connettività al DB (pubblico)."""
    from app.db import engine as db_engine  # noqa: WPS433

    db_status: str = "ok"
    db_error: str | None = None
    try:
        with db_engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        db_status = "error"
        db_error = str(exc)
        logger.error("Health check: database non raggiungibile: %s", exc)

    payload: dict = {
        "app": APP_NAME,
        "version": APP_VERSION,
        "status": "ok" if db_status == "ok" else "degraded",
        "db": db_status,
    }
    if db_error is not None:
        payload["db_error"] = db_error

    status_code: int = 200 if db_status == "ok" else 503
    return JSONResponse(payload, status_code=status_code)