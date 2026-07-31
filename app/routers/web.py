"""Router web dell'applicazione Effort Tracking.

Espone le pagine HTML renderizzate server-side con Jinja2 e gli endpoint
di base (indice, health check). Le route business reali (form di
inserimento, elenco, selezione, export) verranno aggiunte nelle fasi
successive a partire dalla Fase 2.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from pydantic import ValidationError
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config import APP_NAME, APP_VERSION, TEMPLATES_DIR
from app.db import get_db
from app.models import Activity, Client, EffortEntry, Group
from app.schemas.effort import EffortEntryCreate
from fastapi.templating import Jinja2Templates

# Template engine condiviso dal router web.
# I template vivono in app/templates/ (path centralizzato in app/config.py).
templates: Jinja2Templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


router: APIRouter = APIRouter(tags=["web"])


@router.get("/", response_class=HTMLResponse, name="index")
async def index(
    request: Request,
    db: Session = Depends(get_db),
    success: int | None = None,
    error: str | None = None,
) -> HTMLResponse:
    """Pagina principale: form di inserimento + tabella elenco.

    Fase 4: i dropdown del form sono popolati dalle tabelle lookup del DB
    (clients, groups, activities). Il salvataggio (Fase 5), l'elenco dal
    DB (Fase 6) e la selezione record (Fase 7) arrivano in fasi successive.
    `success=1` e `error=descrizione` (query string, set dal POST) mostrano
    rispettivamente il banner di conferma o di errore.
    """
    clients = db.execute(select(Client).order_by(Client.name)).scalars().all()
    groups = db.execute(select(Group).order_by(Group.name)).scalars().all()
    activities = db.execute(select(Activity).order_by(Activity.name)).scalars().all()

    success_message: str | None = None
    if success == 1:
        success_message = "Record salvato correttamente."

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "app_name": APP_NAME,
            "app_version": APP_VERSION,
            "phase": "Fase 5 — Salvataggio record",
            "clients": clients,
            "groups": groups,
            "activities": activities,
            "records": [],  # elenco vuoto per ora; popolato in Fase 6
            "today": date.today().isoformat(),
            "success_message": success_message,
            "error": error,
        },
    )


@router.post("/", response_class=HTMLResponse, name="save_entry")
async def save_entry(
    user: Annotated[str, Form()],
    date: Annotated[date, Form()],
    client_id: Annotated[int, Form(gt=0)],
    group_id: Annotated[int, Form(gt=0)],
    activity_id: Annotated[int, Form(gt=0)],
    hours: Annotated[float, Form()],
    notes: Annotated[str | None, Form()] = None,
    description: Annotated[str | None, Form()] = None,
    action: Annotated[str, Form()] = "single",
    db: Session = Depends(get_db),
) -> RedirectResponse:
    """Salva un nuovo record di effort nel database.

    Fase 5: persistenza reale su `effort_entries`. `action` può essere
    "single" (salvataggio di un singolo record) oppure "week" (copia su
    settimana: crea un record per ogni giorno feriale lun→ven della
    settimana che contiene la data del form). Verifica che l'attività
    richieda una descrizione prima di creare i record.
    """
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
    except ValidationError:
        return RedirectResponse("/?error=validazione", status_code=303)

    activity = db.execute(
        select(Activity).where(Activity.id == payload.activity_id)
    ).scalar_one_or_none()

    # Validazione condizionale: la descrizione è obbligatoria se richiesta.
    if activity is not None and activity.requires_description and not payload.description:
        return RedirectResponse("/?error=descrizione", status_code=303)

    if action == "week":
        return _save_week(payload, db)

    return _save_single(payload, db)


def _save_single(payload: EffortEntryCreate, db: Session) -> RedirectResponse:
    """Crea e salva un singolo record di effort."""
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
    return RedirectResponse("/?success=1", status_code=303)


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