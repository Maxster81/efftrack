"""Configurazione centralizzata del logging dell'applicazione.

Fornisce una funzione `setup_logging()` da chiamare all'avvio (nel
lifespan di `app.main` o prima della creazione dell'app) per
configurare il formato e il livello dei log leggendo da `app.config`.

Il livello è controllabile via env var `EFFORT_TRACKING_LOG_LEVEL`
(default: INFO). Il formato è pensato per essere leggibile sia in
console che in journald (systemd).
"""
from __future__ import annotations

import logging

from app.config import LOG_FORMAT, LOG_LEVEL


def setup_logging() -> None:
    """Configura il logging radice dell'applicazione.

    Idempotente: se chiamata più volte non duplica gli handler.
    Il livello deriva da `EFFORT_TRACKING_LOG_LEVEL` (default INFO).
    """
    root_logger: logging.Logger = logging.getLogger()
    # Evita duplicazione degli handler se la funzione è chiamata due volte.
    if root_logger.handlers:
        return

    handler: logging.StreamHandler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(LOG_FORMAT))
    root_logger.addHandler(handler)

    level: int = getattr(logging, LOG_LEVEL, logging.INFO)
    root_logger.setLevel(level)