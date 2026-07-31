"""Configurazione centralizzata dell'applicazione.

Legge le variabili d'ambiente e fornisce default sicuri per lo sviluppo.
In produzione tutti i secrets devono essere sovrascritti via env vars.
"""
from __future__ import annotations

import os
from pathlib import Path


# --- Path di base -------------------------------------------------------------

# Radice del progetto (cartella che contiene app/).
BASE_DIR: Path = Path(__file__).resolve().parent.parent


# --- Database -----------------------------------------------------------------

# Default: SQLite nella cartella data/ (gitignored).
# Esempio per Postgres futuro: postgresql://user:pwd@host:5432/efftrack
DATABASE_URL: str = os.environ.get(
    "EFFORT_TRACKING_DB_URL",
    f"sqlite:///{BASE_DIR / 'data' / 'efftrack.db'}",
)


# --- Sicurezza (placeholder, auth attiva da Fase 10) -------------------------

# Placeholder esplicito: in produzione va sovrascritto con un valore robusto.
SECRET_KEY: str = os.environ.get(
    "EFFORT_TRACKING_SECRET_KEY",
    "cambia-questa-chiave-prima-di-attivare-l-auth",
)
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = 60


# --- Server -------------------------------------------------------------------

HOST: str = os.environ.get("EFFORT_TRACKING_HOST", "0.0.0.0")
PORT: int = int(os.environ.get("EFFORT_TRACKING_PORT", "8000"))


# --- Costanti applicative -----------------------------------------------------

APP_NAME: str = "Effort Tracking"
APP_VERSION: str = "0.2.0"


# --- Path applicativi (templates, static) ------------------------------------

# Directory dei template Jinja2 (app/templates/).
TEMPLATES_DIR: Path = BASE_DIR / "app" / "templates"

# Directory degli static files (app/static/).
STATIC_DIR: Path = BASE_DIR / "app" / "static"
