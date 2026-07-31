"""Entry point FastAPI dell'applicazione Effort Tracking.

Fase 0–1: bootstrap + pagina HTML statica raggiungibile.
Le route reali (form, salvataggio, elenco, export) verranno aggiunte
nelle fasi successive a partire dalla Fase 2.

Architettura:
- `app/routers/web.py` espone le pagine HTML (root) e l'health check.
- `app/routers/api.py` è un placeholder per le future API JSON
  (prefisso `/api`).
- `app/static/` è montato come directory di file statici.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import APP_NAME, APP_VERSION, STATIC_DIR
from app.db import Base, engine
from app.routers.api import router as api_router
from app.routers.web import router as web_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inizializzazione e shutdown dell'applicazione.

    Allo startup crea le tabelle (idempotente: CREATE TABLE IF NOT EXISTS).
    Nelle fasi 0–1 non ci sono ancora tabelle vere: il Base.metadata
    è vuoto. Il bootstrap diventerà significativo dalla Fase 4.
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

# Registra i router applicativi.
# `web` espone le pagine HTML (root) e l'health check.
# `api` è un prefisso riservato alle future API JSON (vuoto in Fase 1).
app.include_router(web_router)
app.include_router(api_router)