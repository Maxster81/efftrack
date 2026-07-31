"""Router web dell'applicazione Effort Tracking.

Espone le pagine HTML renderizzate server-side con Jinja2 e gli endpoint
di base (indice, health check). Le route business reali (form di
inserimento, elenco, selezione, export) verranno aggiunte nelle fasi
successive a partire dalla Fase 2.
"""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config import APP_NAME, APP_VERSION, TEMPLATES_DIR
from app.db import get_db
from app.models import Activity, Client, Group
from fastapi.templating import Jinja2Templates

# Template engine condiviso dal router web.
# I template vivono in app/templates/ (path centralizzato in app/config.py).
templates: Jinja2Templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


router: APIRouter = APIRouter(tags=["web"])


@router.get("/", response_class=HTMLResponse, name="index")
async def index(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    """Pagina principale: form di inserimento + tabella elenco.

    Fase 4: i dropdown del form sono popolati dalle tabelle lookup del DB
    (clients, groups, activities). Il salvataggio (Fase 5), l'elenco dal
    DB (Fase 6) e la selezione record (Fase 7) arrivano in fasi successive.
    """
    clients = db.execute(select(Client).order_by(Client.name)).scalars().all()
    groups = db.execute(select(Group).order_by(Group.name)).scalars().all()
    activities = db.execute(select(Activity).order_by(Activity.name)).scalars().all()

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "app_name": APP_NAME,
            "app_version": APP_VERSION,
            "phase": "Fase 4 — Database e seed lookup",
            "clients": clients,
            "groups": groups,
            "activities": activities,
            "records": [],  # elenco vuoto per ora; popolato in Fase 6
            # Data odierna come default per nuovi inserimenti.
            "today": date.today().isoformat(),
        },
    )


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