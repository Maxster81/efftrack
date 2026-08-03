"""Router di autenticazione (Fase 10).

Espone login e logout basati su sessione HTTP (cookie firmato da
SessionMiddleware). Le password sono verificate con bcrypt.
"""
from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from passlib.hash import bcrypt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import APP_NAME, APP_VERSION, AUTH_ENABLED, TEMPLATES_DIR
from app.db import get_db
from app.models import User
from app.models.effort_entry import utcnow
from fastapi.templating import Jinja2Templates

logger: logging.Logger = logging.getLogger(__name__)

templates: Jinja2Templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

router: APIRouter = APIRouter(tags=["auth"])


def _login_context(error: str = "") -> dict:
    """Contesto minimo per il template di login (base.html lo richiede)."""
    return {
        "app_name": APP_NAME,
        "app_version": APP_VERSION,
        "phase": "Fase 10 — Autenticazione",
        "auth_enabled": AUTH_ENABLED,
        "current_username": "",
        "error": error,
        "sidebar_items": [],
    }


@router.get("/login", response_class=HTMLResponse, name="login")
async def login_page(request: Request) -> HTMLResponse:
    """Pagina di login (form username/password)."""
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context=_login_context(),
    )


@router.post("/login", response_class=HTMLResponse, name="login_submit")
async def login_submit(
    request: Request,
    username: Annotated[str | None, Form()] = None,
    password: Annotated[str | None, Form()] = None,
    db: Session = Depends(get_db),
) -> Response:
    """Valida le credenziali e crea la sessione utente.

    Se le credenziali sono corrette, salva `user_id` nella sessione e
    redirige a `/`. Altrimenti ri-renderizza la pagina di login con errore.
    """
    if not username or not password:
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context=_login_context("Inserisci username e password."),
        )

    user = db.execute(select(User).where(User.username == username)).scalar_one_or_none()
    if user is None or not bcrypt.verify(password, user.password_hash):
        logger.warning("Tentativo di login fallito per username=%s", username)
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context=_login_context("Credenziali non valide."),
        )

    # Fase 12b: traccia l'ultimo accesso dell'utente.
    user.last_login = utcnow()
    db.commit()

    request.session["user_id"] = user.id
    logger.info("Login riuscito: username=%s (role=%s)", user.username, user.role)
    return RedirectResponse("/", status_code=303)


@router.get("/logout", name="logout")
async def logout(request: Request) -> RedirectResponse:
    """Esegue il logout cancellando la sessione e redirige al login."""
    request.session.clear()
    return RedirectResponse("/login", status_code=303)