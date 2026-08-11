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
# ⚠️ 1.6.0 = prima versione con la dipendenza di sistema `xmlsec1` (SAML).
# Gli update da versioni anteriori richiedono reinstallazione consapevole.
MIN_UPDATE_VERSION="1.6.0"

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

# Helper di input per il wizard: mostra prompt con default, legge la risposta.
# Usa /dev/tty per leggere l'input anche quando lo script è usato con pipe.
# Se /dev/tty non è disponibile (ambiente non interattivo), usa il default.
prompt() {
    local msg="$1" default="$2" answer
    printf "%s [%s]: " "$msg" "$default" >/dev/tty
    if IFS= read -r answer </dev/tty; then
        answer="${answer//[[:space:]]/}"
        echo "${answer:-$default}"
    else
        echo "$default"
    fi
}

prompt_yes() {
    local msg="$1" default="$2" answer
    printf "%s [%s]: " "$msg" "$default" >/dev/tty
    if IFS= read -r answer </dev/tty; then
        answer="$(echo "${answer:-$default}" | tr '[:upper:]' '[:lower:]')"
        case "$answer" in
            s|si|sì|y|yes|1) echo "1" ;;
            *) echo "0" ;;
        esac
    else
        case "$default" in
            Sì|Si|S|YES|Y|1) echo "1" ;;
            *) echo "0" ;;
        esac
    fi
}

# Wizard interattivo: raccoglie le preferenze di configurazione (directory,
# networking, password admin, SAML). Usato durante la creazione del file env.
# Le variabili raccolte vengono usate sia dall'installazione sia dalla
# generazione di /etc/efftrack.env.
wizard_collect() {
    local proxy_host pwd_new
    log "=== Configurazione guidata ==="

    # 1) Directory di installazione (se non specificata con --dir).
    if [ -z "${DEPLOY_DIR_ORIGIN:-}" ] || [ "$DEPLOY_DIR" = "/opt/efftrack" ]; then
        local dir_answer
        dir_answer="$(prompt "Directory di installazione" "${DEPLOY_DIR}")"
        if [ -n "$dir_answer" ] && [ "$dir_answer" != "/opt/efftrack" ]; then
            DEPLOY_DIR="$dir_answer"
            VENV_DIR="${DEPLOY_DIR}/.venv"
        fi
    fi

    # 2) Networking: reverse proxy + porta.
    local proxy_yn
    proxy_yn="$(prompt_yes "L'app sarà dietro un reverse proxy (nginx/Caddy)?" "Sì")"
    if [ "$proxy_yn" = "1" ]; then
        proxy_host="127.0.0.1"
        WIZARD_SESSION_SECURE="true"
    else
        proxy_host="0.0.0.0"
        WIZARD_SESSION_SECURE="false"
    fi
    WIZARD_UVICORN_HOST="$proxy_host"
    WIZARD_UVICORN_PORT="$(prompt "Porta di ascolto" "8000")"

    # 3) Password admin: username fisso "admin", password auto-generata.
    #    La password viene mostrata a video e scritta nel file env come
    #    TEMPORANEA: al primo login l'admin è obbligato a cambiarla.
    WIZARD_ADMIN_USERNAME="admin"
    pwd_new="$(python3 -c 'import secrets,string
alphabet=string.ascii_letters+string.digits+"!@#$%&*+-.=?^"
print("".join(secrets.choice(alphabet) for _ in range(16)))')"
    WIZARD_ADMIN_PASSWORD="$pwd_new"
    echo ""
    echo -e "\033[1;33m  Password temporanea dell'admin generata:\033[0m $pwd_new"
    echo -e "  (copiala per la prima acceduta; al primo login dovrai cambiarla)"
    echo ""

    # 4) SAML / Microsoft Entra ID (opzionale).
    local saml_yn
    saml_yn="$(prompt_yes "Abilitare il login SAML/Microsoft Entra ID?" "No")"
    if [ "$saml_yn" = "1" ]; then
        WIZARD_SAML_ENABLED="true"
        WIZARD_SAML_IDP_ENTITY_ID="$(prompt "Entity ID dell'IdP Microsoft (es. https://sts.windows.net/<tenant-id>/)" "")"
        WIZARD_SAML_IDP_METADATA_URL="$(prompt "URL del metadata XML dell'IdP (federationmetadata.xml)" "")"
        local public_host
        public_host="$(prompt "Hostname pubblico dell'app (es. efftrack.azienda.it)" "")"
        WIZARD_SAML_ENTITY_ID="https://${public_host}/saml/metadata"
        WIZARD_SAML_ACS_URL="https://${public_host}/saml/acs"
        WIZARD_SAML_CERT_FILE=""
        WIZARD_SAML_KEY_FILE=""
    else
        WIZARD_SAML_ENABLED="false"
        WIZARD_SAML_IDP_ENTITY_ID=""
        WIZARD_SAML_IDP_METADATA_URL=""
        WIZARD_SAML_ENTITY_ID="https://efftrack.example.com/saml/metadata"
        WIZARD_SAML_ACS_URL="https://efftrack.example.com/saml/acs"
        WIZARD_SAML_CERT_FILE=""
        WIZARD_SAML_KEY_FILE=""
    fi

    log "Configurazione raccolta."
}

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

# Installa/verifica la dipendenza di sistema `xmlsec1` (richiesta dalla feature
# SAML/MFA: pysaml2 firma/verifica documenti XML-Signature). È una libreria C a
# livello di SISTEMA OPERATIVO, NON coperta da `pip install`: va installata via
# apt. Idempotente: se già presente, non fa nulla.
ensure_xmlsec1() {
    if command -v xmlsec1 >/dev/null 2>&1; then
        log "xmlsec1 già presente ($(xmlsec1 --version 2>/dev/null || echo '?'))."
        return
    fi
    log "Installazione dipendenza di sistema xmlsec1 (per SAML/MFA)..."
    apt-get update -qq
    DEBIAN_FRONTEND=noninteractive apt-get install -y xmlsec1 libxml2-dev libxmlsec1-dev
    log "xmlsec1 installato."
}

# --- 0) Wizard interattivo (prima di installazione ed env) --------------------
# Avvia la raccolta guidata quando si installa o si crea il file env
# (deploy completo, --demo, --install, --env). Non parte per --update,
# --service da solo, o --help.
if [ "${INSTALL_MODE}${ENV_MODE}" != "00" ] && [ "$UPDATE_MODE" = "0" ]; then
    wizard_collect
fi

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

    # Dipendenza di sistema XML-Signature (feature SAML/MFA): va installata a
    # livello OS, NON è coperta da pip. Idempotente.
    ensure_xmlsec1

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
        # Le variabili WIZARD_* sono state raccolte dalla configurazione guidata.
        SECRET="$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')"
        cat > "${ENV_FILE}" <<EOF
# Effort Tracking — ambiente di produzione (generato da deploy.sh + wizard)
# Non committare questo file. Modifica i valori secondo necessità.
EFFORT_TRACKING_SECRET_KEY=${SECRET}
EFFORT_TRACKING_DB_URL=sqlite:///${DEPLOY_DIR}/data/efftrack.db
# Host e porta del web server (li legge uvicorn dalle variabili native
# UVICORN_HOST / UVICORN_PORT, vedi systemd/efftrack.service).
UVICORN_HOST=${WIZARD_UVICORN_HOST:-127.0.0.1}
UVICORN_PORT=${WIZARD_UVICORN_PORT:-8000}
EFFORT_TRACKING_LOG_LEVEL=INFO
EFFORT_TRACKING_AUTH_ENABLED=true
# Modalità demo: true → seed dati di esempio (gruppi, utenti, record di test).
# In produzione (default) resta false → DB pulito con solo l'admin.
EFFORT_TRACKING_DEMO_MODE=${DEMO_VALUE}
EFFORT_TRACKING_ADMIN_USERNAME=${WIZARD_ADMIN_USERNAME:-admin}
# Password TEMPORANEA (generata dal wizard): letta solo al primo seed.
# Al primo login l'admin è obbligato a cambiarla prima di navigare (S11).
EFFORT_TRACKING_ADMIN_PASSWORD=${WIZARD_ADMIN_PASSWORD:-cambia-questa-password}
EFFORT_TRACKING_USER_DELETE_GRACE_DAYS=30
EFFORT_TRACKING_SESSION_SAMESITE=lax
# Durata massima della sessione in secondi (default 30 min).
EFFORT_TRACKING_SESSION_MAX_AGE_SECONDS=1800
# SESSION_SECURE=true richiede HTTPS (il browser scarta il cookie di sessione
# su HTTP). Derivato dal wizard: dietro reverse proxy (127.0.0.1) → true.
EFFORT_TRACKING_SESSION_SECURE=${WIZARD_SESSION_SECURE:-true}
EFFORT_TRACKING_MAX_BODY_BYTES=1048576
# --- SAML / Microsoft Entra ID (opzionale, configurato dal wizard) ---
EFFORT_TRACKING_SAML_ENABLED=${WIZARD_SAML_ENABLED:-false}
EFFORT_TRACKING_SAML_ENTITY_ID=${WIZARD_SAML_ENTITY_ID:-https://efftrack.example.com/saml/metadata}
EFFORT_TRACKING_SAML_ACS_URL=${WIZARD_SAML_ACS_URL:-https://efftrack.example.com/saml/acs}
EFFORT_TRACKING_SAML_IDP_ENTITY_ID=${WIZARD_SAML_IDP_ENTITY_ID:-}
EFFORT_TRACKING_SAML_IDP_METADATA_URL=${WIZARD_SAML_IDP_METADATA_URL:-}
EFFORT_TRACKING_SAML_CERT_FILE=${WIZARD_SAML_CERT_FILE:-}
EFFORT_TRACKING_SAML_KEY_FILE=${WIZARD_SAML_KEY_FILE:-}
EOF
        chmod 600 "${ENV_FILE}"
        log "  Creata ${ENV_FILE} con SECRET_KEY generata e configurazione del wizard."
        if [ "${WIZARD_SAML_ENABLED:-false}" = "true" ]; then
            log "  SAML ABILITATO: verifica di aver configurato Entity ID e metadata correttamente in Azure."
        fi
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
        echo "N.B. Se sei già a una versione >= 1.6.0, questo errore è un bug:" >&2
        echo "     verifica che la versione installata (file DEPLOY_DIR/VERSION) sia" >&2
        echo "     leggibile e formattata come semver (es. 1.6.1)." >&2
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

    # --- 4.6 Dipendenza di sistema xmlsec1 + aggiorna dipendenze ---
    # xmlsec1 (XML-Signature per SAML) è una dipendenza di sistema NON coperta
    # da pip: la installa se manca (idempotente).
    ensure_xmlsec1
    if [ -d "${VENV_DIR}" ]; then
        update_dependencies
    else
        log "⚠ venv non trovato in ${VENV_DIR} — creo un nuovo venv..."
        python3 -m venv "${VENV_DIR}"
        update_dependencies
    fi

    # --- 4.7 Diff nuove variabili d'ambiente (accumula nel report finale) ---
    ENV_NOTICE=""
    if [ -f "${ENV_FILE}" ]; then
        nuove=0
        while IFS='=' read -r var default_val; do
            [ -z "$var" ] && continue
            [[ "$var" =~ ^# ]] && continue
            if ! grep -q "^${var}=" "$ENV_FILE"; then
                if [ "$nuove" = "0" ]; then
                    ENV_NOTICE="  Nuove variabili d'ambiente da aggiungere a ${ENV_FILE}:"
                    nuove=1
                fi
                ENV_NOTICE="${ENV_NOTICE}
    ${var}=${default_val}
      (default: ${default_val} — vedi .env.example per la documentazione)"
            fi
        done < "${DEPLOY_DIR}/.env.example"
        if [ "$nuove" = "0" ]; then
            ENV_NOTICE="  Nessuna nuova variabile d'ambiente: nulla da aggiungere."
        fi
    else
        ENV_NOTICE="  ⚠ ${ENV_FILE} non trovato — nessun confronto variabili possibile."
    fi

    # --- 4.8 Diff service systemd (accumula nel report finale) ---
    SERVICE_NOTICE=""
    if [ -f "/etc/systemd/system/${SERVICE_NAME}" ]; then
        if ! diff -q "${SERVICE_SRC}" "/etc/systemd/system/${SERVICE_NAME}" > /dev/null 2>&1; then
            # Distingue differenze funzionali da soli commenti (#) nell'header.
            # Una riga è "commento" se, dopo <>/spazi, inizia con '#'. Le righe
            # di contesto (spazio) e '---'/'+++' non iniziano con < o >.
            if diff "${SERVICE_SRC}" "/etc/systemd/system/${SERVICE_NAME}" | grep -qE '^[<>][[:space:]]*[^#[:space:]]'; then
                SERVICE_NOTICE="  DIFFERISCE dal template. NON è stato modificato automaticamente.
  Backup dell'attuale: ${BACKUP_DIR}/efftrack.service

  Differenze:
$(diff "${SERVICE_SRC}" "/etc/systemd/system/${SERVICE_NAME}" | sed 's/^/    /')

  Se usi --dir/--env-file personalizzati, adatta WorkingDirectory/ExecStart/
  EnvironmentFile. Se le differenze sono SOLO commenti (righe #) non serve aggiornarlo.
  Dopo eventuali modifiche manuali: sudo systemctl daemon-reload && sudo systemctl restart ${SERVICE_NAME}"
            else
                SERVICE_NOTICE="  Differenze SOLO nei commenti (header): l'unità funzionale è identica,
  non è necessario aggiornare /etc/systemd/system/${SERVICE_NAME}."
            fi
        else
            SERVICE_NOTICE="  File del servizio systemd invariato rispetto al template."
        fi
    else
        SERVICE_NOTICE="  ⚠ ${SERVICE_NAME} non trovato in /etc/systemd/system/."
    fi

    # --- 4.9 Permessi finali ---
    chown -R "${DEPLOY_USER}:${DEPLOY_GROUP}" "${DEPLOY_DIR}"

    # --- 4.10 Riavvia il servizio ---
    log "Avvio il servizio ${SERVICE_NAME}..."
    systemctl start ${SERVICE_NAME}

    health_check

    # --- 4.11 Riepilogo finale (con azioni da valutare) ---
    echo ""
    log "========================================"
    log " Update completato!"
    log " Versione precedente: ${INSTALLED_VERSION}"
    log " Nuova versione:       ${NEW_VERSION}"
    log " Directory app:        ${DEPLOY_DIR}"
    log " File env:             ${ENV_FILE}"
    log " Backup:               ${BACKUP_DIR}/"
    log "========================================"
    echo ""
    log "AZIONI DA VALUTARE:"
    echo ""
    log "  [ Variabili d'ambiente ]"
    echo -e "${ENV_NOTICE}"
    echo ""
    log "  [ Servizio systemd ]"
    echo -e "${SERVICE_NOTICE}"
    echo ""
    log "Il DB non è stato toccato: le migrazioni dello schema (compresa la tabella"
    log "schema_version) girano da sole al primo avvio. Nessuna azione sul database."
    echo ""
    log " Log: sudo journalctl -u ${SERVICE_NAME} -f"
fi

log "Deploy completato."
log "Log del servizio: journalctl -u ${SERVICE_NAME} -f"