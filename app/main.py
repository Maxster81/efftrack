"""Entry point FastAPI dell'applicazione Effort Tracking.

Fase 0–1: bootstrap + pagina HTML statica raggiungibile.
Le route reali (form, salvataggio, elenco, export) sono state aggiunte
nelle fasi successive a partire dalla Fase 2.

Fase 9: logging integrato nel ciclo di vita (startup/shutdown) e uso
della configurazione centralizzata (config.py, .env).

Fase 10: sessione HTTP (SessionMiddleware) e seed dell'utente admin.
Fase 11: migrazione schema (FK user_id, rimozione user_text) e seed
utenti/record di test per la segregazione.

Fase 13a: migrazione campo `disabled` e assegnazione gruppo (admin).

Fase 13b: header di sicurezza HTTP (Issue G) e pagine errore 404/500
(issue A) via exception_handlers.

Architettura:
- `app/routers/web.py` espone le pagine HTML (root) e l'health check.
- `app/routers/auth.py` espone login/logout (sessione).
- `app/routers/admin.py` espone le pagine e azioni di amministrazione.
- `app/routers/api.py` è un placeholder per le future API JSON.
- `app/static/` è montato come directory di file statici.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware

from app.config import APP_NAME, APP_VERSION, DATA_DIR, SECRET_KEY, STATIC_DIR, TEMPLATES_DIR
from app.core.logging_config import setup_logging
from app.core.migrations import run_schema_migrations
from app.core.security_headers import SecurityHeadersMiddleware
from app.core.seed import (
    seed_admin_user,
    seed_lookup_tables,
    seed_test_records,
    seed_test_users,
)
from app.db import Base, SessionLocal, engine
from app.routers.admin import router as admin_router
from app.routers.api import router as api_router
from app.routers.auth import router as auth_router
from app.routers.web import router as web_router

# Import dei modelli: registra le tabelle su Base.metadata così che
# `create_all` (nel lifespan) crei lo schema completo.
import app.models  # noqa: F401,E402

logger: logging.Logger = logging.getLogger(__name__)

# Template engine per gli errori 404/500 (Fase 13b, Issue A).
templates: Jinja2Templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


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

    # Migrazioni controllate (Fase 11): ricrea effort_entries senza user_text
    # e con FK su users.id. Da eseguire PRIMA di create_all per gestire la
    # versione legacy dello schema.
    run_schema_migrations(engine)

    # Crea le tabelle se non esistono (idempotente).
    Base.metadata.create_all(bind=engine)
    logger.info("Schema database verificato (create_all idempotente)")

    # Popola lookup, utente admin e (in sviluppo) utenti/record di test.
    with SessionLocal() as db:
        seed_lookup_tables(db)
        seed_admin_user(db)
        seed_test_users(db)
        seed_test_records(db)

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

# Header di sicurezza HTTP (Fase 13b, Issue G): applicati a ogni risposta.
app.add_middleware(SecurityHeadersMiddleware)


def _error_context(request: Request) -> dict:
    """Contesto condiviso per le pagine di errore, con valori sicuri.

    Funzione sincrona (nessuna operazione I/O): leggerà solo lo username
    dalla sessione, senza query DB.
    """
    current_username = ""
    if hasattr(request, "session"):
        current_username = str(request.session.get("username", ""))
    return {
        "app_name": APP_NAME,
        "app_version": APP_VERSION,
        "phase": "Errore",
        "current_username": current_username,
        "auth_enabled": True,
        "sidebar_items": [],
    }


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> HTMLResponse:
    """Gestisce gli errori HTTP con template HTML coerenti col tema.

    - 404 → 404.html
    - 500 → 500.html
    - altri codici (401, 403, 405, ...) → error.html generico (Fase 13b)
    """
    context = _error_context(request)
    if exc.status_code in (404, 500):
        template_name = f"{exc.status_code}.html"
        level = logger.error if exc.status_code == 500 else logger.warning
        level("%s per %s", exc.status_code, request.url.path)
        return templates.TemplateResponse(
            request=request,
            name=template_name,
            context=context,
            status_code=exc.status_code,
        )
    # Codici generici: contexte arricchito con codice e dettaglio.
    context.update({
        "status_code": exc.status_code,
        "detail": exc.detail,
    })
    logger.warning("%s per %s: %s", exc.status_code, request.url.path, exc.detail)
    return templates.TemplateResponse(
        request=request,
        name="error.html",
        context=context,
        status_code=exc.status_code,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> HTMLResponse:
    """Gestisce gli errori di validazione delle richieste."""
    logger.error("Errore di validazione per %s: %s", request.url.path, exc.errors())
    return templates.TemplateResponse(
        request=request,
        name="500.html",
        context=_error_context(request),
        status_code=500,
    )


# Monta gli static files (CSS, JS, immagini).
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Registra i router applicativi.
# `auth` espone login/logout (sessione).
# `web` espone le pagine HTML (root) e l'health check.
# `admin` espone le pagine e azioni di amministrazione (Fase 13a).
# `api` è un prefisso riservato alle future API JSON.
app.include_router(auth_router)
app.include_router(web_router)
app.include_router(admin_router)
app.include_router(api_router)