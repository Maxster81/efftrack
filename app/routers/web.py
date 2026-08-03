"""Router web dell'applicazione Effort Tracking.

Espone le pagine HTML renderizzate server-side con Jinja2 e gli endpoint
di base (indice, health check). Le route business reali (form di
inserimento, elenco, selezione, export) verranno aggiunte nelle fasi
successive a partire dalla Fase 2.
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

from app.config import APP_NAME, APP_VERSION, TEMPLATES_DIR
from app.db import get_db
from app.models import Activity, Client, EffortEntry, Group
from app.schemas.effort import EffortEntryCreate
from fastapi.templating import Jinja2Templates

logger: logging.Logger = logging.getLogger(__name__)

# Template engine condiviso dal router web.
# I template vivono in app/templates/ (path centralizzato in app/config.py).
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


@router.get("/", response_class=HTMLResponse, name="index")
async def index(
    request: Request,
    db: Session = Depends(get_db),
    success: int | None = None,
    error: str | None = None,
    month: str | None = None,
) -> HTMLResponse:
    """Pagina principale: form di inserimento + tabella elenco.

    Fase 7: la tabella inferiore è popolata dai record di `effort_entries`
    (ordinati per data decrescente) e mostra un dropdown filtro mese/anno
    basato sui mesi distinti presenti nei record. Il parametro `month`
    (es. `?month=2026-07`) filtra i record di quel mese; il mese resta
    derivato da `work_date`, mai persistito. `success`/`error` (set dal
    POST) mostrano i banner. `success=1` = record inserito, `success=2` =
    record aggiornato (Fase 7).
    """
    clients = db.execute(select(Client).order_by(Client.name)).scalars().all()
    groups = db.execute(select(Group).order_by(Group.name)).scalars().all()
    activities = db.execute(select(Activity).order_by(Activity.name)).scalars().all()

    # Mesi distinti presenti nei record, ordinati dal più recente.
    month_rows = db.execute(
        select(func.strftime("%Y-%m", EffortEntry.work_date).label("month"))
        .distinct()
        .order_by(func.strftime("%Y-%m", EffortEntry.work_date).desc())
    ).scalars().all()

    month_options: list[tuple[str, str]] = []
    for m in month_rows:
        anno, num = m.split("-")
        month_options.append((m, f"{_MESI_ITALIANI[int(num)]} {anno}"))

    # Record con filtro mese opzionale, eager load delle relazioni.
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

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "app_name": APP_NAME,
            "app_version": APP_VERSION,
            "phase": "Fase 9b — Toggle dark/light",
            "clients": clients,
            "groups": groups,
            "activities": activities,
            "records": records,
            "month_options": month_options,
            "selected_month": month,
            "today": date.today().isoformat(),
            "success_message": success_message,
            "error": error,
        },
    )


@router.post("/", response_class=HTMLResponse, name="save_entry")
async def save_entry(
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
    db: Session = Depends(get_db),
) -> RedirectResponse:
    """Salva o aggiorna un record di effort nel database.

    Fase 5: persistenza reale su `effort_entries`. `action` può essere
    "single" (salvataggio di un singolo record) oppure "week" (copia su
    settimana: crea un record per ogni giorno feriale lun→ven della
    settimana che contiene la data del form).

    Fase 7: se `record_id` è presente, `action=single` aggiorna il record
    esistente invece di crearne uno nuovo (modalità "modifica"). La copia
    su settimana è pensata solo per l'inserimento (i valori non sono
    validi in modalità modifica). Verifica che l'attività richieda una
    descrizione prima di creare/aggiornare i record. `action=delete`
    elimina definitivamente il record indicato da `record_id` (richiede
    solo l'id, non i campi del form).
    """
    # Eliminazione definitiva: richiede solo `record_id`, non i campi del form.
    if action == "delete":
        return _delete_entry(record_id, db)

    # Costruisce il modello Pydantic per la validazione server-side completa.
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
        return RedirectResponse("/?error=validazione", status_code=303)

    activity = db.execute(
        select(Activity).where(Activity.id == payload.activity_id)
    ).scalar_one_or_none()

    # Validazione condizionale: la descrizione è obbligatoria se richiesta.
    if activity is not None and activity.requires_description and not payload.description:
        logger.warning("Descrizione mancante per attività che la richiede")
        return RedirectResponse("/?error=descrizione", status_code=303)

    # La copia su settimana non è supportata in modalità modifica:
    # se il record è in fase di update, il pulsante "Copia su settimana"
    # viene nascosto lato UI; qui si blocca comunque per sicurezza.
    if action == "week" and record_id is not None:
        return RedirectResponse("/?error=validazione", status_code=303)

    if action == "week":
        return _save_week(payload, db)

    return _save_single(payload, db, record_id=record_id)


def _delete_entry(record_id: int | None, db: Session) -> RedirectResponse:
    """Elimina definitivamente un record di effort dal database.

    Fase 7: con `record_id` valorizzato recupera e cancella il record.
    Se l'id non è presente o il record non esiste, redirect con errore
    di validazione; altrimenti redirect con `?success=3`.
    """
    if record_id is None:
        logger.warning("Eliminazione senza record_id")
        return RedirectResponse("/?error=validazione", status_code=303)

    entry = db.get(EffortEntry, record_id)
    if entry is None:
        logger.warning("Tentativo di eliminazione record inesistente id=%s", record_id)
        return RedirectResponse("/?error=validazione", status_code=303)

    db.delete(entry)
    db.commit()
    logger.info("Record eliminato id=%s", record_id)
    return RedirectResponse("/?success=3", status_code=303)


def _save_single(
    payload: EffortEntryCreate,
    db: Session,
    record_id: int | None = None,
) -> RedirectResponse:
    """Crea un nuovo record oppure aggiorna quello indicato da `record_id`.

    Fase 7: con `record_id` valorizzato, recupera il record esistente e ne
    aggiorna i campi modificabili dal form, poi fa redirect con
    `?success=2`. Se il record non esiste, redirect con errore validazione.
    """
    if record_id is not None:
        entry = db.get(EffortEntry, record_id)
        if entry is None:
            logger.warning("Update di record inesistente id=%s", record_id)
            return RedirectResponse("/?error=validazione", status_code=303)
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
        return RedirectResponse("/?success=2", status_code=303)

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
    return RedirectResponse("/?success=1", status_code=303)


def _save_week(payload: EffortEntryCreate, db: Session) -> RedirectResponse:
    """Copia il form su tutti i giorni feriali della settimana della data."""
    # Lunedì della settimana che contiene la data selezionata (lun=0).
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
    return RedirectResponse("/?success=1", status_code=303)


@router.get("/export", response_class=StreamingResponse, name="export_csv")
async def export_csv(
    db: Session = Depends(get_db),
    month: str | None = None,
) -> StreamingResponse:
    """Esporta i record di effort in formato CSV.

    Fase 8: genera un CSV con le stesse colonne della tabella (Data,
    Cliente, Gruppo, Attività, Utente, Ore, Note, Descrizione attività).
    Il parametro opzionale `month` (es. `?month=2026-07`) filtra i record
    di quel mese; senza filtro vengono esportati tutti i record. La data
    è formattata DD/MM/YYYY. Il file inizia con il BOM UTF-8 per una
    corretta apertura in Excel/Windows.
    """
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
    """Costruisce il contenuto CSV (con BOM UTF-8) dai record di effort.

    Fase 8: le righe seguono l'ordine de `records` così come passato dal
    chiamante (l'endpoint le ordina per data crescente). Header coerente
    con le colonne della tabella. La funzione è separata dall'endpoint
    per renderne il contenuto facilmente testabile senza richieste HTTP.
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
                record.user_text or "",
                record.hours_spent,
                record.notes or "",
                record.description or "",
            ]
        )
    return buffer.getvalue()


@router.get("/health", name="health")
async def health() -> JSONResponse:
    """Health check: stato applicazione + check base della connettività al DB.

    Restituisce 200 con `status: ok` se la connessione al DB risponde,
    altrimenti 503 con `status: degraded` e dettaglio dell'errore.
    """
    # Import lazy per evitare di inizializzare l'engine al solo caricamento
    # del modulo (utile in test e in contesti senza DB).
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