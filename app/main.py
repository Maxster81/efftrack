"""Entry point FastAPI dell'applicazione Effort Tracking.

Fase 0–1: bootstrap + pagina HTML statica raggiungibile.
Le route reali (form, salvataggio, elenco, export) sono state aggiunte
nelle fasi successive a partire dalla Fase 2.

Fase 9: logging integrato nel ciclo di vita (startup/shutdown) e uso
della configurazione centralizzata (config.py, .env).

Fase 10: sessione HTTP (SessionMiddleware) e seed dell'utente admin.

Architettura:
- `app/routers/web.py` espone le pagine HTML (root) e l'health check.
- `app/routers/auth.py` espone login/logout (sessione).
- `app/routers/api.py` è un placeholder per le future API JSON.
- `app/static/` è montato come directory di file statici.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.config import APP_NAME, APP_VERSION, DATA_DIR, SECRET_KEY, STATIC_DIR
from app.core.logging_config import setup_logging
from app.core.seed import seed_admin_user, seed_lookup_tables
from app.db import Base, SessionLocal, engine
from app.routers.api import router as api_router
from app.routers.auth import router as auth_router
from app.routers.web import router as web_router

# Import dei modelli: registra le tabelle su Base.metadata così che
# `create_all` (nel lifespan) crei lo schema completo.
import app.models  # noqa: F401,E402

logger: logging.Logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inizializzazione e shutdown dell'applicazione.

    Allo startup configura il logging (idempotente), crea la cartella
    data/ se assente e le tabelle (CREATE TABLE IF NOT EXISTS), poi
    popola i lookup e l'utente admin. Fase 9-10: logging degli eventi
    chiave del ciclo vita.
    """
    setup_logging()
    logger.info("Avvio %s v%s", APP_NAME, APP_VERSION)

    # Assicura che la cartella data/ esista prima di toccare il DB.
    data_dir: Path = DATA_DIR
    data_dir.mkdir(parents=True, exist_ok=True)

    # Crea le tabelle se non esistono (idempotente).
    Base.metadata.create_all(bind=engine)
    logger.info("Schema database verificato (create_all idempotente)")

    # Popola lookup e utente admin se le tabelle sono vuote.
    with SessionLocal() as db:
        seed_lookup_tables(db)
        seed_admin_user(db)

    logger.info("Avvio completato")
    yield
    logger.info("Arresto %s", APP_NAME)


app: FastAPI = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    lifespan=lifespan,
)

# Sessione HTTP firmata (Fase 10): abilita request.session.
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# Monta gli static files (CSS, JS, immagini).
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Registra i router applicativi.
# `auth` espone login/logout (sessione).
# `web` espone le pagine HTML (root) e l'health check.
# `api` è un prefisso riservato alle future API JSON.
app.include_router(auth_router)
app.include_router(web_router)
app.include_router(api_router)