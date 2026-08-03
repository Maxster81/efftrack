"""Configurazione centralizzata dell'applicazione.

Legge le variabili dal file `.env` (se presente) e dall'ambiente,
fornendo default sicuri per lo sviluppo. In produzione tutti i secrets
devono essere sovrascritti via env vars (o EnvironmentFile systemd).
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# --- Caricamento variabili d'ambiente dal file .env (se esiste) -------------
# Il file .env non va committato (è in .gitignore). Il template di
# riferimento è .env.example. In produzione systemd usa EnvironmentFile.
load_dotenv()


# --- Path di base -------------------------------------------------------------

# Radice del progetto (cartella che contiene app/).
BASE_DIR: Path = Path(__file__).resolve().parent.parent

# Cartella dati (SQLite, export temporanei). Creata a runtime se assente.
DATA_DIR: Path = BASE_DIR / "data"


# --- Database -----------------------------------------------------------------

# Default: SQLite nella cartella data/ (gitignored).
# Esempio per Postgres futuro: postgresql://user:pwd@host:5432/efftrack
DATABASE_URL: str = os.environ.get(
    "EFFORT_TRACKING_DB_URL",
    f"sqlite:///{DATA_DIR / 'efftrack.db'}",
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


# --- Logging ------------------------------------------------------------------

# Livello di log applicativo. Valori tipici: DEBUG, INFO, WARNING, ERROR.
# In produzione consigliato INFO; DEBUG solo per troubleshooting.
LOG_LEVEL: str = os.environ.get("EFFORT_TRACKING_LOG_LEVEL", "INFO").upper()

# Formato del log per un output leggibile in console/journald.
LOG_FORMAT: str = "%(asctime)s %(levelname)s [%(name)s] %(message)s"


# --- Costanti applicative -----------------------------------------------------

APP_NAME: str = "Effort Tracking"
APP_VERSION: str = "0.11.0"


# --- Path applicativi (templates, static) ------------------------------------

# Directory dei template Jinja2 (app/templates/).
TEMPLATES_DIR: Path = BASE_DIR / "app" / "templates"

# Directory degli static files (app/static/).
STATIC_DIR: Path = BASE_DIR / "app" / "static"