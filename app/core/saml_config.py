"""Configurazione del client SAML2 (Service Provider) per EffTrack.

Costruisce il dizionario di configurazione PySAML2 (SP) e inizializza un
client `Saml2Client`. Usato dal router SAML (feature MFA, branch `MFA`).
La configurazione è attiva solo se `SAML_ENABLED` è true e se sono presenti
l'Entity ID dell'IdP e il metadata dell'IdP (Microsoft Entra ID / Azure AD).
"""
from __future__ import annotations

import logging

from saml2 import BINDING_HTTP_POST, BINDING_HTTP_REDIRECT
from saml2.client import Saml2Client
from saml2.config import Config

from app.config import (
    SAML_ACS_URL,
    SAML_CERT_FILE,
    SAML_ENTITY_ID,
    SAML_IDP_ENTITY_ID,
    SAML_IDP_METADATA_URL,
    SAML_KEY_FILE,
)

logger: logging.Logger = logging.getLogger(__name__)


def build_saml_config() -> dict:
    """Dizionario di configurazione dello SP per PySAML2.

    Include Entity ID, endpoint ACS (HTTP-POST), gestione firme/chiavi e il
    metadata dell'IdP (remoto o locale) da cui leggere endpoint SSO e
    certificati di Microsoft.
    """
    return {
        "entityid": SAML_ENTITY_ID,
        "service": {
            "sp": {
                # Firma delle AuthnRequest se lo SP ha una chiave privata.
                "authn_requests_signed": bool(SAML_KEY_FILE),
                # Microsoft Entra ID NON firma il Response esterno (involucro),
                # ma firma l'Assertion interno (dove stanno gli attributi).
                # Richiedere la firma sul Response causa "Signature missing for
                # response" → /login?error=saml-validazione. Va richiesta solo
                # la firma sull'Assertion.
                "want_response_signed": False,
                "want_assertions_signed": True,
                "want_assertions_or_response_signed": True,
                "force_authn": False,
                # Utile per testare direttamente da Azure (SP unsolicited).
                "allow_unsolicited": True,
                "endpoints": {
                    "assertion_consumer_service": [
                        (SAML_ACS_URL, BINDING_HTTP_POST),
                    ],
                },
                "name_id_format": [
                    # NameID come email (UPN) è il formato più comune con Entra ID.
                    "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress",
                    "urn:oasis:names:tc:SAML:2.0:nameid-format:persistent",
                    "urn:oasis:names:tc:SAML:2.0:nameid-format:transient",
                ],
            },
        },
        "key_file": SAML_KEY_FILE or None,
        "cert_file": SAML_CERT_FILE or None,
        # Endpoint SSO, entity ID e certificati dell'IdP vengono letti
        # automaticamente dal metadata di Microsoft (non serve definirli a mano).
        "metadata": {
            "remote": [{"url": SAML_IDP_METADATA_URL}],
        },
        "xmlsec_binary": "/usr/bin/xmlsec1",
        "accepted_time_diff": 60,  # tolleranza sul timestamp (secondi)
        # Timeout (secondi) per le richieste HTTP in uscita del client SAML
        # (es. fetch del metadata IdP remoto). requests/urllib non hanno un
        # timeout di default: senza questo, se rete/proxy è irraggiungibile il
        # login resterebbe appeso all'infinito (la "rotella che gira"). Con un
        # limite prudente il flusso fallisce presto con /login?error=... .
        "http_client_timeout": 20,
    }


def get_saml_client() -> Saml2Client | None:
    """Restituisce il client SAML2 se configurabile, altrimenti None.

    Il client è inizializzabile solo se sono presenti sia l'Entity ID
    dell'IdP sia il metadata. Se mancano, la feature SAML non è usabile e
    si ritorna `None` (nessun crash).
    """
    if not SAML_IDP_ENTITY_ID or not SAML_IDP_METADATA_URL:
        logger.info("SAML: Entity ID IdP o metadata mancanti, login SAML non attivo")
        return None
    try:
        config = Config()
        config.load(build_saml_config())
        return Saml2Client(config=config)
    except Exception as exc:  # noqa: BLE001 - errore applicativo, non fatale
        logger.error("Impossibile inizializzare il client SAML2: %s", exc)
        return None