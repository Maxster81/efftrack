#!/usr/bin/env bash
# =============================================================================
# Effort Tracking — script di deploy ed update (Issue M, Fase 14 + S12)
# =============================================================================
# Questo script automatizza deploy ed update su Ubuntu con systemd. È OPZIONALE
# e flessibile: puoi eseguire tutto, singoli passi, oppure seguire manualmente
# il README. Supporta directory di installazione e file env personalizzati.
#
# Utilizzo:
#   sudo ./deploy.sh                       # deploy completo (install + env + service)
#   sudo ./deploy.sh --install             # solo installazione (codice + venv + dipendenze)
#   sudo ./deploy.sh --env                 # solo creazione file env (se assente)
#   sudo ./deploy.sh --service             # solo installazione servizio systemd
#   sudo ./deploy.sh --demo                # deploy con dati di esempio (solo demo/test)
#   sudo ./deploy.sh --update              # aggiornamento in-place di un'installazione esistente
#   sudo ./deploy.sh --dir /home/efftrack  # directory di installazione personalizzata (tutte le modalità)
#   sudo ./deploy.sh --env-file /etc/efftrack.env  # file env personalizzato (tutte le modalità)
#   sudo ./deploy.sh --help                # mostra questo aiuto
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
SERVICE_NAME="efftrack.service"

# Versione minima da cui è supportato l'update in-place.
# Sotto questa versione bisogna fare backup + reinstallazione.
MIN_UPDATE_VERSION="1.3.0"

# Versione corrente letto dal repo (per il riepilogo).
NEW_VERSION="$(cat VERSION 2>/dev/null || echo '?')"

SERVICE_MODE=0
ENV_MODE=0
INSTALL_MODE=0
UPDATE_MODE=0
HELP_MODE=0
DEMO_MODE=0

# --- Parsing argomenti -------------------------------------------------------
# Supporta --flag con valore (--dir, --env-file) e --flag senza valore.
handle_no_assign() {
    case "$1" in
        --service) SERVICE_MODE=1 ;;
        --env) ENV_MODE=1 ;;
        --install) INSTALL_MODE=1 ;;
        --update) UPDATE_MODE=1 ;;
        --demo) DEMO_MODE=1 ;;
        --help|-h) HELP_MODE=1 ;;
        *) echo "Opzione sconosciuta: $1 (usa --help)" >&2; exit 1 ;;
    esac
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --dir)
            if [[ -z "${2:-}" || "$2" == --* ]]; then
                echo "ERRORE: --dir richiede un path (es. --dir /home/efftrack)" >&2; exit 1
            fi
            DEPLOY_DIR="$2"; VENV_DIR="${DEPLOY_DIR}/.venv"; shift 2 ;;
        --env-file)
            if [[ -z "${2:-}" || "$2" == --* ]]; then
                echo "ERRORE: --env-file richiede un path (es. --env-file /etc/efftrack.env)" >&2; exit 1
            fi
            ENV_FILE="$2"; shift 2 ;;
        *) handle_no_assign "$1"; shift ;;
    esac
done

# Nessuna opzione funzionale = modalità completa (install + env + service).
if [ "${SERVICE_MODE}${ENV_MODE}${INSTALL_MODE}${UPDATE_MODE}${HELP_MODE}" = "00000" ]; then
    INSTALL_MODE=1
    ENV_MODE=1
    SERVICE_MODE=1
fi

if [ "$HELP_MODE" = "1" ]; then
    sed -n '1,40p' "$0" | sed 's/^# \{0,1\}//'
    exit 0
fi

if [ "$(id -u)" != "0" ]; then
    echo "ERRORE: eseguire con sudo/root (almeno per installare il servizio)." >&2
    exit 1
fi

log() { echo -e "\n\033[1;32m[deploy]\033[0m $*"; }

# --- Funzioni condivise ------------------------------------------------------

rsync_code() {
    local extra_excludes=("$@")
    log "Copia del codice nell'area di deploy ${DEPLOY_DIR}..."
    # Sorgente: cartella corrente (radice del repo). Esclude file inutili/dev.
    # Extra excludes in arrivo da chiamante (es. 'backups' in update).
    local rsync_args=(-a --delete --exclude '.git' --exclude '.venv'
        --exclude '__pycache__' --exclude '*.pyc' --exclude '.env'
        --exclude 'data' --exclude 'memory-bank' --exclude 'tests'
        --exclude '.pytest_cache')
    for exc in "${extra_excludes[@]}"; do
        rsync_args+=(--exclude "$exc")
    done
    rsync "${rsync_args[@]}" ./ "${DEPLOY_DIR}/"

    # Ricrea sempre la cartella data/ (richiesta da ReadWritePaths del service
    # systemd PRIMA dell'avvio, altrimenti errore 226/NAMESPACE) e i permessi.
    log "Creazione directory dati ${DEPLOY_DIR}/data..."
    mkdir -p "${DEPLOY_DIR}/data"
    chown -R "${DEPLOY_USER}:${DEPLOY_GROUP}" "${DEPLOY_DIR}"
}

update_dependencies() {
    log "Aggiornamento dipendenze in ${VENV_DIR}..."
    "${VENV_DIR}/bin/pip" install --upgrade pip
    "${VENV_DIR}/bin/pip" install -r "${DEPLOY_DIR}/requirements.txt"
    log "Dipendenze aggiornate."
}

health_check() {
    log "Health check..."
    sleep 2
    # Host/porta letti dal file env se presente, altrimenti default.
    local hport="${UVICORN_PORT:-8000}"
    if [ -f "${ENV_FILE}" ]; then
        hport="$(grep -E '^UVICORN_PORT=' "${ENV_FILE}" | cut -d= -f2- || echo 8000)"
    fi
    curl -s -o /dev/null -w "HTTP %{http_code}\n" "http://127.0.0.1:${hport}/health" || true
}

get_installed_version() {
    if [ -f "${DEPLOY_DIR}/VERSION" ]; then
        cat "${DEPLOY_DIR}/VERSION"
    else
        echo ""
    fi
}

# --- 1) Installazione (venv + dipendenze + copia file) -----------------------
if [ "$INSTALL_MODE" = "1" ]; then
    log "Creazione utente di sistema ${DEPLOY_USER} (se non esiste)..."
    if ! id "${DEPLOY_USER}" &>/dev/null; then
        useradd --system --home "${DEPLOY_DIR}" --shell /usr/sbin/nologin "${DEPLOY_USER}"
    fi

    log "Creazione directory ${DEPLOY_DIR} e permessi..."
    mkdir -p "${DEPLOY_DIR}"
    chown -R "${DEPLOY_USER}:${DEPLOY_GROUP}" "${DEPLOY_DIR}"

    rsync_code

    log "Creazione venv (se assente)..."
    if [ ! -d "${VENV_DIR}" ]; then
        python3 -m venv "${VENV_DIR}"
    fi

    update_dependencies

    log "Permessi finali sulla directory di deploy..."
    chown -R "${DEPLOY_USER}:${DEPLOY_GROUP}" "${DEPLOY_DIR}"
fi

# --- 2) Creazione file env di produzione -------------------------------------
# Valorizza EFFORT_TRACKING_DEMO_MODE in base al flag --demo.
DEMO_VALUE="false"
if [ "$DEMO_MODE" = "1" ]; then
    DEMO_VALUE="true"
fi

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
# Modalità demo: true → seed dati di esempio (gruppi, utenti, record di test).
# In produzione (default) resta false → DB pulito con solo l'admin.
EFFORT_TRACKING_DEMO_MODE=${DEMO_VALUE}
EFFORT_TRACKING_ADMIN_USERNAME=admin
# CAMBIA QUESTA PASSWORD PRIMA DI ANDARE IN PRODUZIONE!
# NOTA (S11): questa password è TEMPORANEA, letta solo al primo seed.
# Al primo login l'admin è obbligato a cambiarla prima di navigare.
EFFORT_TRACKING_ADMIN_PASSWORD=cambia-questa-password
EFFORT_TRACKING_USER_DELETE_GRACE_DAYS=30
EFFORT_TRACKING_SESSION_SAMESITE=lax
# NOTA: SESSION_SECURE=true richiede HTTPS (il browser scarta il cookie di
# sessione su HTTP). Su pre-prod/sviluppo senza TLS impostarlo a false.
# In produzione dietro reverse proxy con TLS (es. NetScaler) va rimesso a true.
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
    systemctl enable ${SERVICE_NAME}
    systemctl restart ${SERVICE_NAME}

    log "Verifica dello stato..."
    systemctl status ${SERVICE_NAME} --no-pager || true

    health_check
fi

# --- 4) Update in-place ------------------------------------------------------
if [ "$UPDATE_MODE" = "1" ]; then
    log "=== Modalità update ==="

    # --- 4.1 Precondizioni ---
    if [ ! -d "${DEPLOY_DIR}" ]; then
        echo "ERRORE: nessuna installazione trovata in ${DEPLOY_DIR}." >&2
        echo "Se è la prima installazione, usa: sudo ./deploy.sh --install [--dir ${DEPLOY_DIR}] [--env-file ${ENV_FILE}]" >&2
        exit 1
    fi
    if [ ! -f "/etc/systemd/system/${SERVICE_NAME}" ]; then
        echo "ERRORE: unità systemd ${SERVICE_NAME} non trovata in /etc/systemd/system/." >&2
        echo "Installa prima il servizio (--install o --service) oppure verifica il nome unità." >&2
        exit 1
    fi

    # --- 4.2 Versione installata e compatibilità ---
    INSTALLED_VERSION="$(get_installed_version)"
    if [ -z "$INSTALLED_VERSION" ]; then
        echo "ERRORE: impossibile determinare la versione installata (manca ${DEPLOY_DIR}/VERSION)." >&2
        exit 1
    fi
    log "Versione installata: ${INSTALLED_VERSION} — Minima per update: ${MIN_UPDATE_VERSION}"

    # Confronto semver (rust-style: confronto punto per punto i numeri).
    # Ritorna 0 se a >= b, 1 altrimenti.
    version_ok() {
        local a="$1" b="$2"
        local ia ib na nb
        IFS='.' read -ra ia <<< "$a"
        IFS='.' read -ra ib <<< "$b"
        for i in 0 1 2; do
            na="${ia[$i]:-0}"
            nb="${ib[$i]:-0}"
            if (( 10#$na > 10#$nb )); then return 0; fi
            if (( 10#$na < 10#$nb )); then return 1; fi
        done
        return 0
    }

    if version_ok "$INSTALLED_VERSION" "$MIN_UPDATE_VERSION"; then
        log "Update supportato."
    else
        echo ""
        echo "==============================================================" >&2
        echo "  ERRORE: update NON eseguito." >&2
        echo "  Versione installata:        ${INSTALLED_VERSION}" >&2
        echo "  Versione minima supportata: ${MIN_UPDATE_VERSION} (soglia in deploy.sh)" >&2
        echo "==============================================================" >&2
        echo "" >&2
        echo "Lo script si è FERMATO qui: non ha modificato alcun file." >&2
        echo "" >&2
        echo "Procedura CONSIGLIATA — backup e reinstallazione (per versioni sotto soglia):" >&2
        echo "  1. Ferma il servizio:     sudo systemctl stop ${SERVICE_NAME}" >&2
        echo "  2. Backup del DB:         sudo cp ${DEPLOY_DIR}/data/efftrack.db /backup/sicuro/" >&2
        echo "  3. Backup env:            sudo cp ${ENV_FILE} /backup/sicuro/" >&2
        echo "  4. Rimuovi installazione: sudo rm -rf ${DEPLOY_DIR}" >&2
        echo "  5. Clona nuovo repo ed esegui: sudo ./deploy.sh --install --dir ${DEPLOY_DIR} --env-file ${ENV_FILE}" >&2
        echo "  6. Ferma il servizio, ripristina DB ed env dai backup, riavvia" >&2
        echo "  7. Al primo avvio le migrazioni porteranno il DB alla versione corrente" >&2
        echo "" >&2
        echo "N.B. Se sei già a una versione >= 1.3.0, questo errore è un bug:" >&2
        echo "     verifica che la versione installata (file DEPLOY_DIR/VERSION) sia" >&2
        echo "     leggibile e formattata come semver (es. 1.3.2)." >&2
        exit 1
    fi

    # --- 4.3 Backup automatico dei file critici ---
    BACKUP_DIR="${DEPLOY_DIR}/backups/$(date +%Y%m%d-%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    log "Backup in ${BACKUP_DIR}"

    # DB: path derivato dall'env se presente, altrimenti default.
    DB_PATH="${DEPLOY_DIR}/data/efftrack.db"
    if [ -f "${ENV_FILE}" ]; then
        dburl="$(grep -E '^EFFORT_TRACKING_DB_URL=' "${ENV_FILE}" | cut -d= -f2- || true)"
        if [[ "$dburl" == sqlite:///* ]]; then
            DB_PATH="${dburl#sqlite:///}"
        fi
    fi
    if [ -f "$DB_PATH" ]; then
        cp "$DB_PATH" "$BACKUP_DIR/efftrack.db"
        log "  ✓ Backup DB: $BACKUP_DIR/efftrack.db"
    else
        log "  ⚠ DB non trovato in $DB_PATH — backup manuale richiesto."
    fi

    if [ -f "${ENV_FILE}" ]; then
        cp "${ENV_FILE}" "$BACKUP_DIR/efftrack.env"
        log "  ✓ Backup env: $BACKUP_DIR/efftrack.env"
    else
        log "  ⚠ Env non trovato in ${ENV_FILE} — backup ignorato."
    fi

    if [ -f "/etc/systemd/system/${SERVICE_NAME}" ]; then
        cp "/etc/systemd/system/${SERVICE_NAME}" "$BACKUP_DIR/efftrack.service"
        log "  ✓ Backup service: $BACKUP_DIR/efftrack.service"
    fi

    # --- 4.4 Ferma il servizio ---
    log "Fermo il servizio ${SERVICE_NAME}..."
    systemctl stop ${SERVICE_NAME}

    # --- 4.5 Copia nuovo codice (esclude anche backups/) ---
    rsync_code "backups"

    # --- 4.6 Aggiorna dipendenze ---
    if [ -d "${VENV_DIR}" ]; then
        update_dependencies
    else
        log "⚠ venv non trovato in ${VENV_DIR} — creo un nuovo venv..."
        python3 -m venv "${VENV_DIR}"
        update_dependencies
    fi

    # --- 4.7 Diff nuove variabili d'ambiente ---
    log "Controllo nuove variabili d'ambiente rispetto a ${ENV_FILE}..."
    if [ -f "${ENV_FILE}" ]; then
        nuove=0
        while IFS='=' read -r var default_val; do
            [ -z "$var" ] && continue
            [[ "$var" =~ ^# ]] && continue
            if ! grep -q "^${var}=" "$ENV_FILE"; then
                if [ "$nuove" = "0" ]; then
                    echo ""
                    echo "  Nuove variabili d'ambiente da aggiungere a ${ENV_FILE}:"
                    echo ""
                    nuove=1
                fi
                echo "    $var=${default_val}"
                echo "      (default: ${default_val} — vedi .env.example per la documentazione)"
                echo ""
            fi
        done < "${DEPLOY_DIR}/.env.example"

        if [ "$nuove" = "0" ]; then
            log "  Nessuna nuova variabile d'ambiente da segnalare."
        else
            log "  L'app usa già i default interni (config.py): il servizio funziona"
            log "  anche senza aggiungerle. Aggiungile a ${ENV_FILE} solo se vuoi"
            log "  personalizzarle, poi riavvia il servizio."
        fi
    else
        log "  ⚠ ${ENV_FILE} non trovato — nessun confronto variabili possibile."
    fi

    # --- 4.8 Diff service systemd ---
    if [ -f "/etc/systemd/system/${SERVICE_NAME}" ]; then
        if ! diff -q "${SERVICE_SRC}" "/etc/systemd/system/${SERVICE_NAME}" > /dev/null 2>&1; then
            echo ""
            log "⚠️  ATTENZIONE: il file del servizio systemd è cambiato nella nuova versione."
            log "⚠️  /etc/systemd/system/${SERVICE_NAME} (attuale)"
            log "⚠️  differisce da ${SERVICE_SRC} (nuovo)."
            log "⚠️  IL FILE NON È STATO MODIFICATO."
            log "⚠️  Backup dell'attuale: ${BACKUP_DIR}/efftrack.service"
            echo ""
            log "Differenze:"
            diff "${SERVICE_SRC}" "/etc/systemd/system/${SERVICE_NAME}" || true
            echo ""
            log "Nota: se usi una directory di installazione personalizzata (--dir)"
            log "o un file env personalizzato (--env-file), aggiorna di conseguenza"
            log "WorkingDirectory/ExecStart/EnvironmentFile nel service."
            echo ""
            log "Dopo aver aggiornato manualmente il file, esegui:"
            log "  sudo systemctl daemon-reload"
            log "  sudo systemctl restart ${SERVICE_NAME}"
            echo ""
        else
            log "File del servizio systemd invariato. ✓"
        fi
    fi

    # --- 4.9 Permessi finali ---
    chown -R "${DEPLOY_USER}:${DEPLOY_GROUP}" "${DEPLOY_DIR}"

    # --- 4.10 Riavvia il servizio ---
    log "Avvio il servizio ${SERVICE_NAME}..."
    systemctl start ${SERVICE_NAME}

    health_check

    # --- 4.11 Riepilogo ---
    echo ""
    log "========================================"
    log " Update completato!"
    log " Versione precedente: ${INSTALLED_VERSION}"
    log " Nuova versione:       ${NEW_VERSION}"
    log " Directory app:        ${DEPLOY_DIR}"
    log " File env:             ${ENV_FILE}"
    log " Backup:               ${BACKUP_DIR}/"
    log "========================================"
    log " Log: sudo journalctl -u ${SERVICE_NAME} -f"
fi

log "Deploy completato."
log "Log del servizio: journalctl -u ${SERVICE_NAME} -f"