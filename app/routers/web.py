"""Router web dell'applicazione Effort Tracking.

Espone le pagine HTML renderizzate server-side con Jinja2 e gli endpoint
di base (indice, health check). Dalla Fase 10 le route business sono
protette: se l'autenticazione è attiva e non c'è una sessione valida,
l'utente viene rediretto al login.

Il campo User del form, quando autenticato, è precompilato e forzato
lato server con lo username della sessione (readonly lato client).
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
from sqlalchemy import func, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, selectinload
from fastapi.templating import Jinja2Templates

from app.config import APP_NAME, APP_VERSION, AUTH_ENABLED, TEMPLATES_DIR
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


def _with_month(base_url: str, month: str | None) -> str:
    """Aggiunge il parametro month a un URL se presente (Issue 1: filtri)."""
    if month:
        separator: str = "&" if "?" in base_url else "?"
        return f"{base_url}{separator}month={month}"
    return base_url


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

    clients = db.execute(select(Client).order_by(Client.name)).scalars().all()
    groups = db.execute(select(Group).order_by(Group.name)).scalars().all()
    activities = db.execute(select(Activity).order_by(Activity.name)).scalars().all()

    month_rows = db.execute(
        select(func.strftime("%Y-%m", EffortEntry.work_date).label("month"))
        .distinct()
        .order_by(func.strftime("%Y-%m", EffortEntry.work_date).desc())
    ).scalars().all()

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
        )
        .order_by(EffortEntry.work_date.desc())
    )
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

    # In Fase 10, con auth attiva, l'utente corrente è sempre loggato qui.
    current_username: str = user.username if user is not None else ""

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "app_name": APP_NAME,
            "app_version": APP_VERSION,
            "phase": "Fase 10 — Autenticazione",
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
    """
    redirect = _require_auth(current_user)
    if redirect is not None:
        return redirect

    # Con auth attiva, rispetta sempre l'utente della sessione (il campo
    # User è readonly lato client, ma qui se ne garantisce l'integrità).
    if AUTH_ENABLED and current_user is not None:
        user = current_user.username

    # Eliminazione definitiva: richiede solo `record_id`.
    if action == "delete":
        return _delete_entry(record_id, db, month)

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
        return _save_week(payload, db, month)

    return _save_single(payload, db, record_id=record_id, month=month)


def _delete_entry(record_id: int | None, db: Session, month: str | None = None) -> RedirectResponse:
    """Elimina definitivamente un record di effort dal database."""
    if record_id is None:
        logger.warning("Eliminazione senza record_id")
        return RedirectResponse(_with_month("/?error=validazione", month), status_code=303)

    entry = db.get(EffortEntry, record_id)
    if entry is None:
        logger.warning("Tentativo di eliminazione record inesistente id=%s", record_id)
        return RedirectResponse(_with_month("/?error=validazione", month), status_code=303)

    db.delete(entry)
    db.commit()
    logger.info("Record eliminato id=%s", record_id)
    return RedirectResponse(_with_month("/?success=3", month), status_code=303)


def _save_single(
    payload: EffortEntryCreate,
    db: Session,
    record_id: int | None = None,
    month: str | None = None,
) -> RedirectResponse:
    """Crea un nuovo record oppure aggiorna quello indicato da `record_id`."""
    if record_id is not None:
        entry = db.get(EffortEntry, record_id)
        if entry is None:
            logger.warning("Update di record inesistente id=%s", record_id)
            return RedirectResponse(_with_month("/?error=validazione", month), status_code=303)
        entry.user_text = payload.user
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
        user_id=None,
        user_text=payload.user,
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


def _save_week(payload: EffortEntryCreate, db: Session, month: str | None = None) -> RedirectResponse:
    """Copia il form su tutti i giorni feriali della settimana della data."""
    monday = payload.date - timedelta(days=payload.date.weekday())
    for offset in range(5):  # lun, mar, mer, gio, ven
        db.add(
            EffortEntry(
                user_id=None,
                user_text=payload.user,
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
    """Esporta i record di effort in formato CSV (protetta)."""
    redirect = _require_auth(user)
    if redirect is not None:
        return redirect

    stmt = (
        select(EffortEntry)
        .options(
            selectinload(EffortEntry.client),
            selectinload(EffortEntry.group),
            selectinload(EffortEntry.activity),
        )
        .order_by(EffortEntry.work_date.asc())
    )
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
    """Costruisce il contenuto CSV (con BOM UTF-8) dai record di effort."""
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
                record.user_text or "",
                record.hours_spent,
                record.notes or "",
                record.description or "",
            ]
        )
    return buffer.getvalue()


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