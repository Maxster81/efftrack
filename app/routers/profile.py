"""Router per la pagina profilo utente.

Consente all'utente loggato di visualizzare e modificare i propri dati
anagrafici (nome, cognome, email) e di cambiare la password.

Predispone `password_change_required` per un futuro flusso di cambio
password obbligatorio al primo login.
"""
from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from passlib.hash import bcrypt
from pydantic import ValidationError
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates

from app.config import APP_NAME, APP_VERSION, AUTH_ENABLED, TEMPLATES_DIR
from app.core.permissions import is_admin, is_manager
from app.db import get_db
from app.dependencies import get_current_user
from app.models import User
from app.schemas.effort import ProfileUpdate, SelfPasswordChange

logger: logging.Logger = logging.getLogger(__name__)

templates: Jinja2Templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

router: APIRouter = APIRouter(prefix="/profile", tags=["profile"])


def _require_auth(user: User | None) -> RedirectResponse | None:
    """Blocco di autenticazione: redirige al login se non c'è un utente."""
    if AUTH_ENABLED and user is None:
        return RedirectResponse("/login", status_code=303)
    return None


def _sidebar_items(user: User) -> list[dict[str, str]]:
    """Voci della sidebar in base al ruolo (stessa logica di web.py)."""
    if is_admin(user):
        return [
            {"label": "Dashboard", "href": "/admin"},
            {"label": "Registrazioni", "href": "/admin/records"},
            {"label": "Gestione Utenti", "href": "/admin/users"},
            {"label": "Gestione Lookup", "href": "/admin/lookup"},
        ]
    items: list[dict[str, str]] = [
        {"label": "Registrazioni", "href": "/"},
    ]
    if is_manager(user):
        items.append({"label": "Gruppo", "href": "/group"})
    items.append({"label": "Profilo", "href": "/profile"})
    return items


@router.get("", response_class=HTMLResponse, name="profile")
async def profile_page(
    request: Request,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
) -> HTMLResponse:
    """Pagina profilo utente: mostra nome, cognome, email e form cambio password."""
    redirect = _require_auth(user)
    if redirect is not None:
        return redirect
    assert user is not None

    # Ricarica l'utente dalla sessione corrente per avere i dati freschi.
    fresh_user = db.get(User, user.id)
    assert fresh_user is not None

    return templates.TemplateResponse(
        request=request,
        name="profile.html",
        context={
            "app_name": APP_NAME,
            "app_version": APP_VERSION,
            "phase": "Profilo Utente",
            "auth_enabled": AUTH_ENABLED,
            "current_username": fresh_user.username,
            "sidebar_items": _sidebar_items(fresh_user),
            "first_name": fresh_user.first_name or "",
            "last_name": fresh_user.last_name or "",
            "email": fresh_user.email or "",
            "password_change_required": fresh_user.password_change_required,
            # Banner di esito operazioni (query string).
            "profile_ok": request.query_params.get("profile_ok"),
            "profile_err": request.query_params.get("profile_err"),
            "pwd_ok": request.query_params.get("pwd_ok"),
            "pwd_err": request.query_params.get("pwd_err"),
        },
    )


@router.post("", name="profile_update")
async def profile_update(
    request: Request,
    first_name: Annotated[str | None, Form()] = None,
    last_name: Annotated[str | None, Form()] = None,
    email: Annotated[str | None, Form()] = None,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
) -> RedirectResponse:
    """Aggiorna i dati anagrafici del profilo (nome, cognome, email)."""
    redirect = _require_auth(user)
    if redirect is not None:
        return redirect
    assert user is not None

    fresh_user = db.get(User, user.id)
    assert fresh_user is not None

    try:
        data = ProfileUpdate(
            first_name=first_name,
            last_name=last_name,
            email=email,
        )
    except ValidationError as exc:
        errors = "; ".join(
            f"{'.'.join(str(p) for p in e['loc'])}: {e['msg']}" for e in exc.errors()
        )
        logger.warning(
            "Validazione profilo fallita per utente=%s: %s", fresh_user.username, errors,
        )
        return RedirectResponse(
            f"/profile?profile_err={errors}", status_code=303,
        )

    fresh_user.first_name = data.first_name
    fresh_user.last_name = data.last_name
    fresh_user.email = data.email
    db.commit()

    logger.info(
        "Profilo aggiornato per utente=%s (first_name=%s, last_name=%s, email=%s)",
        fresh_user.username, fresh_user.first_name, fresh_user.last_name, fresh_user.email,
    )
    return RedirectResponse("/profile?profile_ok=1", status_code=303)


@router.post("/change-password", name="profile_change_password")
async def profile_change_password(
    request: Request,
    current_password: Annotated[str | None, Form()] = None,
    new_password: Annotated[str | None, Form()] = None,
    confirm_password: Annotated[str | None, Form()] = None,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
) -> RedirectResponse:
    """Cambia la password dell'utente loggato.

    Richiede la password attuale, la nuova password e la conferma.
    """
    redirect = _require_auth(user)
    if redirect is not None:
        return redirect
    assert user is not None

    fresh_user = db.get(User, user.id)
    assert fresh_user is not None

    # Verifica che tutti i campi siano presenti.
    if not current_password or not new_password or not confirm_password:
        return RedirectResponse(
            "/profile?pwd_err=Tutti i campi sono obbligatori.", status_code=303,
        )

    # Verifica che la password attuale sia corretta.
    if not bcrypt.verify(current_password, fresh_user.password_hash):
        logger.warning(
            "Cambio password fallito (password attuale errata) per utente=%s",
            fresh_user.username,
        )
        return RedirectResponse(
            "/profile?pwd_err=Password attuale non corretta.", status_code=303,
        )

    # Validazione della nuova password via Pydantic.
    try:
        data = SelfPasswordChange(
            current_password=current_password,
            new_password=new_password,
        )
    except ValidationError as exc:
        errors = "; ".join(
            f"{'.'.join(str(p) for p in e['loc'])}: {e['msg']}" for e in exc.errors()
        )
        return RedirectResponse(
            f"/profile?pwd_err={errors}", status_code=303,
        )

    # Verifica che nuova password e conferma coincidano.
    if data.new_password != confirm_password:
        return RedirectResponse(
            "/profile?pwd_err=Le due password non coincidono.", status_code=303,
        )

    # Aggiorna l'hash della password.
    fresh_user.password_hash = bcrypt.hash(data.new_password)
    # Se il flag password_change_required era attivo, lo azzera
    # (il cambio è avvenuto con successo).
    if fresh_user.password_change_required:
        fresh_user.password_change_required = False
    db.commit()

    logger.info("Password cambiata con successo per utente=%s", fresh_user.username)
    return RedirectResponse("/profile?pwd_ok=1", status_code=303)