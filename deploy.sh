#!/usr/bin/env bash
# =============================================================================
# Effort Tracking — script di deploy opzionale (Issue M, Fase 14)
# =============================================================================
# Questo script automatizza il deploy su Ubuntu con systemd. È OPZIONALE:
# puoi eseguirlo tutto oppure solo i passi che ti servono. In alternativa,
# segui manualmente i passi documentati nel README e nel service file.
#
# Utilizzo:
#   sudo ./deploy.sh                 # deploy completo (consigliato)
#   sudo ./deploy.sh --install       # solo installazione (venv + dipendenze)
#   sudo ./deploy.sh --service       # solo installazione del servizio systemd
#   sudo ./deploy.sh --env           # solo creazione /etc/efftrack.env
#   sudo ./deploy.sh --help          # mostra questo aiuto
#
# Prerequisiti:
#   - Ubuntu con systemd
#   - Run come root (sudo)
#   - Git repo clonato nella directory corrente
# =============================================================================
set -euo pipefail

APP_NAME="efftrack"
DEPLOY_USER="efftrack"
DEPLOY_GROUP="efftrack"
DEPLOY_DIR="/opt/efftrack"
ENV_FILE="/etc/efftrack.env"
VENV_DIR="${DEPLOY_DIR}/.venv"
SERVICE_SRC="systemd/efftrack.service"
SERVICE_DST="/etc/systemd/system/efftrack.service"

SERVICE_MODE=0
ENV_MODE=0
INSTALL_MODE=0
HELP_MODE=0

# --- Parsing argomenti -------------------------------------------------------
for arg in "$@"; do
    case "$arg" in
        --service) SERVICE_MODE=1 ;;
        --env) ENV_MODE=1 ;;
        --install) INSTALL_MODE=1 ;;
        --help|-h) HELP_MODE=1 ;;
        *) echo "Opzione sconosciuta: $arg (usa --help)" >&2; exit 1 ;;
    esac
done

# Nessuna opzione = modalità completa.
if [ "${SERVICE_MODE}${ENV_MODE}${INSTALL_MODE}${HELP_MODE}" = "0000" ]; then
    INSTALL_MODE=1
    ENV_MODE=1
    SERVICE_MODE=1
fi

if [ "$HELP_MODE" = "1" ]; then
    sed -n '1,30p' "$0" | sed 's/^# \{0,1\}//'
    exit 0
fi

if [ "$(id -u)" != "0" ]; then
    echo "ERRORE: eseguire con sudo/root (almeno per installare il servizio)." >&2
    exit 1
fi

log() { echo -e "\n\033[1;32m[deploy]\033[0m $*"; }

# --- 1) Installazione (venv + dipendenze + copia file) -----------------------
if [ "$INSTALL_MODE" = "1" ]; then
    log "Creazione utente di sistema ${DEPLOY_USER} (se non esiste)..."
    if ! id "${DEPLOY_USER}" &>/dev/null; then
        useradd --system --home "${DEPLOY_DIR}" --shell /usr/sbin/nologin "${DEPLOY_USER}"
    fi

    log "Creazione directory ${DEPLOY_DIR} e permessi..."
    mkdir -p "${DEPLOY_DIR}"
    chown -R "${DEPLOY_USER}:${DEPLOY_GROUP}" "${DEPLOY_DIR}"

    log "Copia del codice nell'area di deploy..."
    # Sorgente: cartella corrente (radice del repo). Esclude file inutili/devi.
    rsync -a --delete \
        --exclude '.git' \
        --exclude '.venv' \
        --exclude '__pycache__' \
        --exclude '*.pyc' \
        --exclude '.env' \
        --exclude 'data' \
        --exclude 'memory-bank' \
        --exclude 'tests' \
        --exclude '.pytest_cache' \
        ./ "${DEPLOY_DIR}/"

    # Ricrea sempre la cartella data/ (richiesta da ReadWritePaths del service
    # systemd PRIMA dell'avvio, altrimenti errore 226/NAMESPACE) e i permessi.
    log "Creazione directory dati ${DEPLOY_DIR}/data..."
    mkdir -p "${DEPLOY_DIR}/data"
    chown "${DEPLOY_USER}:${DEPLOY_GROUP}" "${DEPLOY_DIR}/data"

    log "Creazione venv (se assente)..."
    if [ ! -d "${VENV_DIR}" ]; then
        python3 -m venv "${VENV_DIR}"
    fi

    log "Installazione dipendenze in ${VENV_DIR}..."
    "${VENV_DIR}/bin/pip" install --upgrade pip
    "${VENV_DIR}/bin/pip" install -r "${DEPLOY_DIR}/requirements.txt"

    log "Permessi finali sulla directory di deploy..."
    chown -R "${DEPLOY_USER}:${DEPLOY_GROUP}" "${DEPLOY_DIR}"
fi

# --- 2) Creazione file env di produzione -------------------------------------
if [ "$ENV_MODE" = "1" ]; then
    log "Creazione ${ENV_FILE} se assente (non sovrascrive)..."
    if [ -f "${ENV_FILE}" ]; then
        log "  ${ENV_FILE} esiste già: non lo sovrascrivo."
    else
        # Genera una SECRET_KEY robusta e imposta valori di produzione sicuri.
        SECRET="$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')"
        cat > "${ENV_FILE}" <<EOF
# Effort Tracking — ambiente di produzione (generato da deploy.sh)
# Non committare questo file. Modifica i valori secondo necessità.
EFFORT_TRACKING_SECRET_KEY=${SECRET}
EFFORT_TRACKING_DB_URL=sqlite:///${DEPLOY_DIR}/data/efftrack.db
# Host e porta del web server (li legge uvicorn dalle variabili native
# UVICORN_HOST / UVICORN_PORT, vedi systemd/efftrack.service).
UVICORN_HOST=127.0.0.1
UVICORN_PORT=8000
EFFORT_TRACKING_LOG_LEVEL=INFO
EFFORT_TRACKING_AUTH_ENABLED=true
EFFORT_TRACKING_ADMIN_USERNAME=admin
# CAMBIA QUESTA PASSWORD PRIMA DI ANDARE IN PRODUZIONE!
# NOTA (S11): questa password è TEMPORANEA, letta solo al primo seed.
# Al primo login l'admin è obbligato a cambiarla prima di navigare.
EFFORT_TRACKING_ADMIN_PASSWORD=cambia-questa-password
EFFORT_TRACKING_USER_DELETE_GRACE_DAYS=30
EFFORT_TRACKING_SESSION_SAMESITE=lax
EFFORT_TRACKING_SESSION_SECURE=true
EFFORT_TRACKING_MAX_BODY_BYTES=1048576
EOF
        chmod 600 "${ENV_FILE}"
        log "  Creata ${ENV_FILE} con SECRET_KEY generata. RIVEDI la password admin!"
    fi
fi

# --- 3) Installazione e avvio servizio systemd -------------------------------
if [ "$SERVICE_MODE" = "1" ]; then
    log "Verifica dell'unità systemd sorgente..."
    if [ ! -f "${SERVICE_SRC}" ]; then
        echo "ERRORE: manca ${SERVICE_SRC} (esegui dalla root del repo)." >&2
        exit 1
    fi

    log "Copia unità systemd in ${SERVICE_DST}..."
    cp "${SERVICE_SRC}" "${SERVICE_DST}"

    log "Ricarica, abilita e avvia il servizio..."
    systemctl daemon-reload
    systemctl enable efftrack.service
    systemctl restart efftrack.service

    log "Verifica dello stato..."
    systemctl status efftrack.service --no-pager || true

    log "Health check..."
    sleep 2
    curl -s -o /dev/null -w "HTTP %{http_code}\n" http://127.0.0.1:8000/health || true
fi

log "Deploy completato."
log "Log del servizio: journalctl -u efftrack -f"