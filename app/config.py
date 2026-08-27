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


# --- Sicurezza (autenticazione) ---------------------------------------------

# Placeholder esplicito: in produzione va sovrascritto con un valore robusto.
SECRET_KEY: str = os.environ.get(
    "EFFORT_TRACKING_SECRET_KEY",
    "cambia-questa-chiave-prima-di-attivare-l-auth",
)
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

# Attivazione auth. Se False, il web server resta pubblico (utile in sviluppo/test).
AUTH_ENABLED: bool = os.environ.get("EFFORT_TRACKING_AUTH_ENABLED", "true").lower() in ("1", "true", "yes", "on")

# Modalità demo (seed dati di esempio: lookup, gruppi, utenti e record di test).
# In produzione resta False (DB pulito, solo admin). L'opzione --demo di
# deploy.sh imposta questa variabile a true per ambienti di demo/test.
DEMO_MODE: bool = os.environ.get("EFFORT_TRACKING_DEMO_MODE", "false").lower() in ("1", "true", "yes", "on")

# Credenziali del primo utente amministratore creato al bootstrap.
# Usate solo se la tabella users è vuota. In produzione vanno sovrascritte via env.
ADMIN_USERNAME: str = os.environ.get("EFFORT_TRACKING_ADMIN_USERNAME", "admin")
ADMIN_PASSWORD: str = os.environ.get("EFFORT_TRACKING_ADMIN_PASSWORD", "admin")

# Giorni minimi di disabilitazione prima che un utente possa essere eliminato
# definitivamente (insieme ai suoi record). Configurabile.
USER_DELETE_GRACE_DAYS: int = int(
    os.environ.get("EFFORT_TRACKING_USER_DELETE_GRACE_DAYS", "30")
)

# Parametri di sicurezza del cookie di sessione.
# `SameSite` del cookie: "lax" protegge dai CSRF cross-site (default Starlette).
# `SECURE`: in produzione dietro TLS va impostato a "1" (cookie solo via HTTPS).
SESSION_COOKIE_SAMESITE: str = os.environ.get(
    "EFFORT_TRACKING_SESSION_SAMESITE", "lax"
).lower()
SESSION_COOKIE_SECURE: bool = os.environ.get(
    "EFFORT_TRACKING_SESSION_SECURE", "false"
).lower() in ("1", "true", "yes", "on")
# Durata massima della sessione in secondi. Default 30 minuti: se un utente
# chiude il browser senza logout, la sessione scade e rientra al login.
SESSION_MAX_AGE_SECONDS: int = int(
    os.environ.get("EFFORT_TRACKING_SESSION_MAX_AGE_SECONDS", "1800")
)

# Limite massimo della dimensione del body delle richieste in byte.
# Protegge da payload maliziosi o eccessivi. Default 1 MiB (1_048_576 byte).
MAX_BODY_BYTES: int = int(
    os.environ.get("EFFORT_TRACKING_MAX_BODY_BYTES", "1048576")
)


# --- SAML (Microsoft Entra ID / Azure AD) ------------------------------------

# Attivazione del login SAML. Se False, il login resta solo locale
# (nessun impatto sugli ambienti esistenti). Feature in sviluppo su branch MFA.
SAML_ENABLED: bool = os.environ.get(
    "EFFORT_TRACKING_SAML_ENABLED", "false"
).lower() in ("1", "true", "yes", "on")

# Entity ID dello SP (EffTrack): deve combaciare con l'Identifier configurato in Azure.
SAML_ENTITY_ID: str = os.environ.get(
    "EFFORT_TRACKING_SAML_ENTITY_ID",
    "https://efftrack.example.com/saml/metadata",
)

# Endpoint ACS pubblico di EffTrack (Reply URL in Azure).
SAML_ACS_URL: str = os.environ.get(
    "EFFORT_TRACKING_SAML_ACS_URL",
    "https://efftrack.example.com/saml/acs",
)

# Entity ID dell'IdP (Microsoft). Forma tipica: https://sts.windows.net/<tenant-id>/
SAML_IDP_ENTITY_ID: str = os.environ.get("EFFORT_TRACKING_SAML_IDP_ENTITY_ID", "")

# Metadata dell'IdP: URL remoto o percorso file locale (il metadata XML contiene
# endpoint SSO, entity ID e certificati di Microsoft).
SAML_IDP_METADATA_URL: str = os.environ.get("EFFORT_TRACKING_SAML_IDP_METADATA_URL", "")

# Certificato e chiave dello SP (per firmare AuthnRequest, se richiesto).
SAML_CERT_FILE: str = os.environ.get("EFFORT_TRACKING_SAML_CERT_FILE", "")
SAML_KEY_FILE: str = os.environ.get("EFFORT_TRACKING_SAML_KEY_FILE", "")


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
APP_VERSION: str = "1.9.3"


# --- Path applicativi (templates, static) ------------------------------------

# Directory dei template Jinja2 (app/templates/).
TEMPLATES_DIR: Path = BASE_DIR / "app" / "templates"

# Directory degli static files (app/static/).
STATIC_DIR: Path = BASE_DIR / "app" / "static"