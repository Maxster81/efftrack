"""Router di autenticazione.

Espone login e logout basati su sessione HTTP (cookie firmato da
SessionMiddleware). Le password sono verificate con bcrypt.
"""
from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import APP_NAME, APP_VERSION, AUTH_ENABLED, SAML_ENABLED, TEMPLATES_DIR
from app.core.password import verify_password
from app.core.permissions import is_admin
from app.db import get_db
from app.models import User
from app.models.effort_entry import utcnow
from fastapi.templating import Jinja2Templates

logger: logging.Logger = logging.getLogger(__name__)

templates: Jinja2Templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

router: APIRouter = APIRouter(tags=["auth"])

# Messaggi utente leggibili per gli errori del flusso SAML (SAML-8).
# Il parametro `?error=...` usato nei redirect SAML è una chiave tecnica;
# qui la traduciamo in testo chiaro per il login.html.
_SAML_ERROR_MESSAGES: dict[str, str] = {
    "saml-non-configurato": "Il login Microsoft non è configurato. Contatta l'amministratore.",
    "saml-generazione": "Errore nel collegamento con Microsoft. Riprova.",
    "saml-validazione": "La risposta di Microsoft non può essere verificata. Riprova.",
    "saml-utente-non-attivo": "Questo account non è autorizzato al login.",
    "saml-interno": "Errore interno nel login Microsoft. Riprova.",
}


def _login_error_message(error_key: str) -> str:
    """Traduce una chiave di errore (query string) in messaggio leggibile.

    Se la chiave non è nota, la restituisce tale e quale (fallback sicuro).
    """
    return _SAML_ERROR_MESSAGES.get(error_key, error_key)


def _login_context(error: str = "", info: str = "") -> dict:
    """Contesto minimo per il template di login (base.html lo richiede)."""
    return {
        "app_name": APP_NAME,
        "app_version": APP_VERSION,
        "phase": "Autenticazione",
        "auth_enabled": AUTH_ENABLED,
        # Mostra il pulsante "Accedi con Microsoft" se il login SAML è attivo
        # (feature MFA, branch MFA).
        "saml_enabled": SAML_ENABLED,
        "current_username": "",
        "error": error,
        # Banner informativo di successo (es. dopo il cambio password forzato).
        "info": info,
        "sidebar_items": [],
        # Nasconde hamburger e sidebar nella pagina pubblica di login.
        "hide_nav": True,
    }


@router.get("/login", response_class=HTMLResponse, name="login")
async def login_page(
    request: Request,
    error: str | None = Query(None),
    password_changed: str | None = Query(None),
) -> HTMLResponse:
    """Pagina di login (form username/password).

    Accetta `?error=<chiave>` (es. usata dai redirect SAML) e la traduce in
    un messaggio leggibile per l'utente. Con `?password_changed=1` (arrivo dopo
    il logout forzato a seguito di un cambio password, PWD-LOGOUT) mostra un
    banner informativo.
    """
    info = ""
    if password_changed == "1":
        info = "Password aggiornata. Accedi di nuovo con la nuova password."
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context=_login_context(_login_error_message(error) if error else "", info),
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
    if user is None or not verify_password(password, user.password_hash):
        logger.warning("Tentativo di login fallito per username=%s", username)
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context=_login_context("Credenziali non valide."),
        )

    # Account disabilitato → login bloccato.
    if user.disabled:
        logger.warning("Login rifiutato: account disabilitato per username=%s", username)
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context=_login_context("Account disabilitato. Contatta l'amministratore."),
        )

    # Traccia l'ultimo accesso dell'utente.
    user.last_login = utcnow()
    db.commit()

    request.session["user_id"] = user.id
    request.session["username"] = user.username
    logger.info("Login riuscito: username=%s (role=%s)", user.username, user.role)

    # Cambio password obbligatorio al primo login: l'utente va su /profile
    # finché non cambia la password temporanea (vedi PasswordChangeRequiredMiddleware).
    if user.password_change_required:
        return RedirectResponse("/profile", status_code=303)

    # L'admin atterra sulla dashboard /admin.
    if is_admin(user):
        return RedirectResponse("/admin", status_code=303)
    return RedirectResponse("/", status_code=303)


@router.get("/logout", name="logout")
async def logout(request: Request) -> RedirectResponse:
    """Esegue il logout cancellando la sessione e redirige al login."""
    request.session.clear()
    return RedirectResponse("/login", status_code=303)