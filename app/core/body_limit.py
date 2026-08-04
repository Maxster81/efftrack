"""Middleware Starlette per la limitazione della dimensione del body.

Applicato globalmente tramite `app.add_middleware`, rifiuta le richieste
il cui corpo supera una soglia configurabile. Il limite default è 1 MB,
più che sufficiente per i form di effort tracking. Protegge il server da
richieste maliziose molto grandi.
"""
from __future__ import annotations

import logging
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger: logging.Logger = logging.getLogger(__name__)


class RequestBodyLimitMiddleware(BaseHTTPMiddleware):
    """Limita la dimensione massima del body di ogni richiesta.

    Le richieste con `Content-Length` oltre la soglia vengono rifiutate
    con HTTP 413. Per le richieste con transfer-encoding chunked (senza
    Content-Length) si assume che il limite sia verificato a monte dal
    server HTTP; il controllo qui copre il caso standard.
    """

    __slots__ = ("max_body_bytes",)

    def __init__(self, app, max_body_bytes: int) -> None:
        """Inizializza il middleware con la soglia massima in byte."""
        super().__init__(app)
        self.max_body_bytes: int = max_body_bytes

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Verifica la dimensione del body ed eventualmente la rifiuta."""
        content_length: str | None = request.headers.get("content-length")
        if content_length is not None:
            try:
                length: int = int(content_length)
            except ValueError:
                logger.warning("Content-Length non valido: %s", content_length)
                return Response("Content-Length non valido", status_code=400)
            if length > self.max_body_bytes:
                logger.warning(
                    "Rifiutata richiesta troppo grande: %d byte (limite %d) per %s",
                    length,
                    self.max_body_bytes,
                    request.url.path,
                )
                return Response(
                    "Corpo della richiesta troppo grande",
                    status_code=413,
                )
        return await call_next(request)