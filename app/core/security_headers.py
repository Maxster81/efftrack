"""Middleware per l'aggiunta degli header di sicurezza HTTP.

Aggiunge a ogni risposta HTTP gli header raccomandati per la sicurezza:
- `X-Content-Type-Options: nosniff`  → impedisce il MIME-sniffing
- `X-Frame-Options: DENY`            → impedisce il clickjacking
- `Content-Security-Policy`          → CSP di base (permette inline per stili/script,
  necessari per lo script anti-FOUC nel <head> e per eventuali stili inline)
- `Strict-Transport-Security`        → HSTS (utile in produzione)
"""
from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Aggiunge gli header di sicurezza a ogni risposta HTTP."""

    _CSP = (
        "default-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "script-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "form-action 'self'"
    )

    _HEADERS: dict[str, str] = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Content-Security-Policy": _CSP,
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Referrer-Policy": "no-referrer",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    }

    async def dispatch(self, request: Request, call_next) -> Response:
        response: Response = await call_next(request)
        for key, value in self._HEADERS.items():
            # Non sovrascrive header già impostati (es. da altre fonti).
            if key not in response.headers:
                response.headers[key] = value
        return response