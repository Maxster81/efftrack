"""Entry point FastAPI dell'applicazione Effort Tracking.

Fase 0: bootstrap. Espone solo una pagina indice di benvenuto e l'health check.
Le route reali (form, salvataggio, elenco) verranno aggiunte nelle fasi successive.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.config import APP_NAME, APP_VERSION
from app.db import Base, engine

# Cartella dei template e degli static.
TEMPLATES_DIR: Path = Path(__file__).resolve().parent / "templates"
STATIC_DIR: Path = Path(__file__).resolve().parent / "static"

templates: Jinja2Templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inizializzazione e shutdown dell'applicazione.

    Allo startup crea le tabelle (idempotente: CREATE TABLE IF NOT EXISTS).
    In Fase 0 non ci sono tabelle vere: il Base.metadata è vuoto.
    """
    # Assicura che la cartella data/ esista prima di toccare il DB.
    data_dir: Path = Path(__file__).resolve().parent.parent / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    # Crea le tabelle se non esistono (idempotente).
    Base.metadata.create_all(bind=engine)
    yield
    # Niente cleanup specifico allo shutdown per ora.


app: FastAPI = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    lifespan=lifespan,
)

# Monta gli static files (CSS, JS, immagini).
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", response_class=HTMLResponse, name="index")
async def index(request: Request) -> HTMLResponse:
    """Pagina di benvenuto della Fase 0."""
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "app_name": APP_NAME,
            "app_version": APP_VERSION,
            "phase": "Fase 0 — Bootstrap",
        },
    )


@app.get("/health", name="health")
async def health() -> JSONResponse:
    """Health check: stato applicazione + check base della connettività al DB."""
    db_status: str = "ok"
    db_error: str | None = None
    try:
        with engine.connect() as connection:
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
