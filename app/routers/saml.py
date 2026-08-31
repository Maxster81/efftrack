"""Router per l'autenticazione SAML (Microsoft Entra ID / Azure AD).

Espone gli endpoint del Service Provider (SP):
- GET  /saml/login     → redirige a Microsoft (AuthnRequest)
- POST /saml/acs       → riceve la SAML Response, la valida e crea la sessione
- GET  /saml/metadata  → metadati XML dello SP (utile per l'IdP)
- GET  /saml/logout    → logout locale (niente Single Logout SAML nella prima versione)

La feature è attiva solo se SAML_ENABLED=true e se il client PySAML2 è
inizializzabile (vedi app/core/saml_config.py). Se non configurato, gli
endpoint redirigono al login locale con un messaggio d'errore.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from saml2 import BINDING_HTTP_POST, BINDING_HTTP_REDIRECT
from sqlalchemy.orm import Session

from app.config import SAML_ENABLED, SAML_IDP_ENTITY_ID
from app.core.saml_config import get_saml_client
from app.db import get_db
from app.models.effort_entry import utcnow
from app.services.saml_user import setup_user_from_saml

logger: logging.Logger = logging.getLogger(__name__)

router: APIRouter = APIRouter(prefix="/saml", tags=["saml"])


@router.get("/login", name="saml_login", response_model=None)
async def saml_login(request: Request) -> RedirectResponse | HTMLResponse:
    """Avvia il flusso SAML redirigendo a Microsoft.

    Genera una AuthnRequest e redirige il browser all'IdP (Microsoft). Il
    binding usato è deciso da PySAML2 in base al metadata dell'IdP:
    - HTTP-POST   → restituisce una pagina HTML con form auto-submit
      (il JS fa submit immediato verso Microsoft).
    - HTTP-Redirect → risponde con un redirect 302 (Location).
    Salva il `req_id` in sessione per validare la risposta all'ACS (anti-replay).
    """
    client = get_saml_client()
    if not SAML_ENABLED or client is None:
        logger.warning("Tentativo di login SAML ma feature non configurata")
        return RedirectResponse("/login?error=saml-non-configurato", status_code=302)

    try:
        # Sceglie l'endpoint SSO dell'IdP dal metadata (HTTP-POST o REDIRECT).
        # Microsoft richiede la risposta SAML via HTTP-POST. Per rispettare
        # il vincolo, usiamo HTTP-POST per la AuthnRequest (primo nella lista).
        binding, destination = client.pick_binding(
            "single_sign_on_service",
            [BINDING_HTTP_POST, BINDING_HTTP_REDIRECT],
            entity_id=SAML_IDP_ENTITY_ID,
        )
        req_id, authn_request = client.create_authn_request(
            destination=destination,
            binding=binding,
        )
        # Nota: request.url_for() restituisce un oggetto URL (Starlette) il cui
        # .replace() non è compatibile con PySAML2 (in Python 3.14). Va
        # convertito a stringa prima di passarlo come relay_state.
        http_args = client.apply_binding(
            binding,
            str(authn_request),
            destination,
            relay_state=str(request.url_for("index")),
        )
    except Exception as exc:  # noqa: BLE001 - errore di generazione, non fatale
        logger.error("Errore generazione AuthnRequest SAML: %s", exc)
        return RedirectResponse("/login?error=saml-generazione", status_code=302)

    # Salva la richiesta pendente per validare la risposta (anti-replay).
    # Nota: la sessione ha vita limitata (SESSION_MAX_AGE_SECONDS), quindi
    # se l'utente resta su Microsoft troppo a lungo la risposta non troverà
    # la richiesta → errore gestito in /acs.
    request.session["saml_pending"] = {req_id: str(request.url_for("index"))}

    # Binding HTTP-POST: PySAML2 (http_form_post_message in saml2/pack.py)
    # restituisce in http_args["data"] l'HTML COMPLETO del form auto-submit
    # (<body onload="document.forms[0].submit()">) con action=http_args["url"]
    # e i campi hidden SAMLRequest/RelayState. Va servito così com'è: il
    # browser lo carica e il JS fa submit immediato verso Microsoft.
    if binding == BINDING_HTTP_POST:
        logger.info("AuthnRequest SAML generata verso IdP (HTTP-POST) a %s", destination)
        return HTMLResponse(content=http_args["data"])

    # Binding HTTP-Redirect: PySAML2 restituisce la Location negli headers.
    location = http_args["headers"][0][1]
    logger.info("AuthnRequest SAML generata verso IdP (HTTP-Redirect) a %s", destination)
    return RedirectResponse(location, status_code=302)


@router.post("/acs", name="saml_acs")
async def saml_acs(
    request: Request,
    SAMLResponse: str = Form(...),
    RelayState: str = Form(""),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    """Riceve la SAML Response da Microsoft, la valida e crea la sessione.

    Dopo la validazione della firma/condizioni, risolve o crea l'utente
    (SAML-5) e imposta la medesima sessione HTTP del login locale.
    """
    client = get_saml_client()
    if not SAML_ENABLED or client is None:
        logger.warning("ACS SAML chiamato ma feature non configurata")
        return RedirectResponse("/login?error=saml-non-configurato", status_code=302)

    pending = request.session.get("saml_pending", {})
    try:
        authn_response = client.parse_authn_request_response(
            SAMLResponse,
            BINDING_HTTP_POST,
            outstanding=pending,
        )
    except Exception as exc:  # noqa: BLE001 - errori di validazione SAML
        logger.warning("Validazione risposta SAML fallita: %s", exc)
        request.session.pop("saml_pending", None)
        return RedirectResponse("/login?error=saml-validazione", status_code=302)

    try:
        identity = authn_response.ava  # attributi, es. {"email": [...], "displayName": [...]}
        name_id = authn_response.name_id.text if authn_response.name_id is not None else ""
        request.session.pop("saml_pending", None)

        # Risolve o crea l'utente (SAML-5) e imposta la sessione.
        user = setup_user_from_saml(db, name_id, identity)
        if user is None:
            logger.warning("SAML: impossibile risolvere/creare utente (name_id=%s)", name_id)
            return RedirectResponse("/login?error=saml-utente-non-attivo", status_code=302)

        # Account disabilitato → login bloccato (coerente con il login locale).
        if user.disabled:
            logger.warning("Login SAML rifiutato: account disabilitato per username=%s", user.username)
            return RedirectResponse("/login?error=saml-utente-non-attivo", status_code=302)

        # Traccia l'ultimo accesso dell'utente (coerente con il login locale).
        user.last_login = utcnow()
        db.commit()

        request.session["user_id"] = user.id
        request.session["username"] = user.username
    except Exception as exc:  # noqa: BLE001 - errore inatteso, non deve esporre 500
        logger.exception("Errore inatteso nell'ACS SAML: %s", exc)
        request.session.pop("saml_pending", None)
        return RedirectResponse("/login?error=saml-interno", status_code=302)

    logger.info("Login SAML riuscito: username=%s (role=%s)", user.username, user.role)
    return RedirectResponse("/", status_code=303)


@router.get("/metadata", name="saml_metadata")
async def saml_metadata(request: Request) -> HTMLResponse:
    """Espone i metadati XML dello SP (Entity Descriptor).

    Utili per configurare l'applicazione (Enterprise Application) su
    Microsoft Entra ID, o per usare lo schema automatico dell'IdP.
    """
    from saml2.config import Config
    from saml2.metadata import create_metadata_string

    from app.core.saml_config import build_saml_config

    if not SAML_ENABLED:
        return HTMLResponse("SAML non configurato", status_code=404)

    config = Config()
    config.load(build_saml_config())
    # Nota (pysaml2 7.5.4): create_metadata_string richiede `configfile` come primo
    # parametro posizionale obbligatorio; se `config` (oggetto Config) è fornito,
    # il file viene ignorato. Passiamo una stringa vuota come placeholder.
    xml = create_metadata_string(configfile="", config=config, sign=False)
    return HTMLResponse(content=xml, media_type="application/xml")


@router.get("/logout", name="saml_logout")
async def saml_logout(request: Request) -> RedirectResponse:
    """Logout locale: cancella la sessione e redirige al login.

    Single Logout SAML (SLO) non implementato in questa versione: il logout
    della sessione è sufficiente per l'utente.
    """
    request.session.clear()
    return RedirectResponse("/login", status_code=303)