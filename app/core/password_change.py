"""Middleware per il cambio password obbligatorio al primo login (S11).

Protegge tutte le route: se un utente con sessione attiva ha il flag
`password_change_required=True`, viene rediretto a `/profile` finché non
cambia la password temporanea. Whitelist per profilo/logout/login/static/
health/docs.

Implementazione: middleware **puro** (non `BaseHTTPMiddleware`). Starlette
`SessionMiddleware` popola `scope["session"]` nello scope originale; un
`BaseHTTPMiddleware` fa un clone dello scope e perde la sessione (o la ricrea
vuota). Un middleware puro legge `scope["session"]` direttamente, senza
clonazione, così vede la sessione caricata da `SessionMiddleware` registrato
come più esterno.
"""
from __future__ import annotations

import logging
from typing import Callable
from urllib.parse import quote

from starlette.requests import Request
from starlette.responses import RedirectResponse, Response

from app.config import AUTH_ENABLED
from app.db import SessionLocal
from app.models import User

logger: logging.Logger = logging.getLogger(__name__)

# Percorsi sempre raggiungibili anche con password_change_required attivo.
_WHITELIST_EXACT: frozenset[str] = frozenset({
    "/profile",
    "/profile/change-password",
    "/logout",
    "/login",
    "/health",
    "/docs",
    "/openapi.json",
})

_WHITELIST_PREFIXES: tuple[str, ...] = ("/static/", "/docs/", "/saml/")


def _is_whitelisted(path: str) -> bool:
    """True se il path è nella whitelist (esatto o per prefisso)."""
    if path in _WHITELIST_EXACT:
        return True
    return any(path.startswith(prefix) for prefix in _WHITELIST_PREFIXES)


class PasswordChangeRequiredMiddleware:
    """Redirige a /profile gli utenti con password temporanea non cambiata.

    Middleware puro (in stile Starlette `__call__`), che NON clona lo scope:
    legge `scope["session"]` direttamente, già popolato da `SessionMiddleware`
    (registrato come middleware più esterno in `main.py`).
    """

    def __init__(self, app) -> None:
        """Memorizza l'applicazione sottostante."""
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        """Intercetta le richieste HTTP e blocca se il flag è attivo."""
        if not AUTH_ENABLED or scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        session = scope.get("session")
        if not session:
            # Utente anonimo o sessione non ancora caricata: lascia passare.
            await self.app(scope, receive, send)
            return

        user_id = session.get("user_id")
        if user_id is None:
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        if _is_whitelisted(path):
            await self.app(scope, receive, send)
            return

        with SessionLocal() as db:
            user = db.get(User, user_id)
            if user is None or not user.password_change_required:
                await self.app(scope, receive, send)
                return

        logger.info(
            "Accesso bloccato: utente id=%s deve cambiare password (path=%s)",
            user_id,
            path,
        )
        # Include il percorso tentato (URL-encoded, anche le '/', così il valore
        # del parametro query resta non ambiguo) così la pagina profilo può
        # comunicare all'utente quale azione è stata bloccata dal middleware.
        redirect = RedirectResponse(f"/profile?pwd_blocked={quote(path, safe='')}", status_code=303)
        await redirect(scope, receive, send)