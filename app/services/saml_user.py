"""Servizio per la risoluzione/creazione dell'utente dopo l'accesso SAML.

Implementa la logica di associazione (SAML-5, feature MFA):
- Ramo 1: esiste già un utente associato a questa identità SAML → login diretto.
- Ramo 2: esiste un utente locale con la stessa email/UPN → associa i campi SAML.
- Ramo 3: nessuna corrispondenza → crea un nuovo utente (username=email/UPN,
  password_hash segnaposto, role="user").

Gli utenti SAML NON devono essere bloccati dal middleware di cambio password:
in tutti i rami `password_change_required` viene forzato a `False`.
L'admin (senza campi SAML) non viene mai coinvolto (SAML-D2).
"""
from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import SAML_IDP_ENTITY_ID
from app.models import User

logger: logging.Logger = logging.getLogger(__name__)

# Segnaposto per utenti senza password locale (il login locale non è possibile).
_NO_LOCAL_PASSWORD: str = "!"


def setup_user_from_saml(
    db: Session,
    name_id: str,
    attributes: dict | None = None,
) -> User | None:
    """Trova o crea l'utente associato all'identità SAML.

    `name_id` è l'UPN (email) dell'utente fornito da Microsoft. Gli attributi
    (nome, cognome) vengono usati per arricchire il profilo se disponibili.
    Ritorna `None` se `name_id` è vuoto o se `SAML_IDP_ENTITY_ID` non è
    configurato.
    """
    if not name_id:
        logger.warning("SAML: name_id mancante, impossibile risolvere l'utente")
        return None
    if not SAML_IDP_ENTITY_ID:
        logger.warning("SAML: Entity ID IdP non configurato, utente non risolvibile")
        return None

    attributes = attributes or {}

    # Ramo 1: utente già associato a questa identità SAML.
    user = db.execute(
        select(User).where(
            User.saml_entity_id == SAML_IDP_ENTITY_ID,
            User.saml_name_id == name_id,
        )
    ).scalar_one_or_none()
    if user is not None:
        # Il superuser non può mai avere controparte SAML (SUPERUSER-ADMIN).
        if user.is_superuser:
            logger.warning("SAML: accesso al superuser rifiutato (username=%s)", user.username)
            return None
        _ensure_saml_ok(db, user, attributes, associato=True)
        return user

    # Ramo 2: utente locale con la stessa email/UPN → associa i campi SAML.
    # Match su email OPPURE username, in due query separate e semplici: l'UPN
    # da Microsoft coincide con l'email aziendale, ma l'admin potrebbe aver
    # creato l'utente senza email (email=None) usando proprio l'UPN come
    # username (SAML-D1). Senza questa ricerca su username il ramo 3
    # proverebbe un INSERT con lo stesso username → UNIQUE constraint failed.
    user = db.execute(
        select(User).where(User.email == name_id)
    ).scalar_one_or_none()
    if user is None:
        user = db.execute(
            select(User).where(User.username == name_id)
        ).scalar_one_or_none()
    if user is not None:
        # Il superuser è solo locale: mai associarlo a un'identità SAML (SUPERUSER-ADMIN).
        if user.is_superuser:
            logger.warning("SAML: associazione al superuser rifiutata (username=%s)", user.username)
            return None
        user.saml_entity_id = SAML_IDP_ENTITY_ID
        user.saml_name_id = name_id
        db.commit()  # l'associazione va sempre persistita, anche se _ensure_saml_ok non ha altre modifiche
        _ensure_saml_ok(db, user, attributes, associato=True)
        logger.info("SAML: utente locale %s associato all'identità SAML", user.username)
        return user

    # Ramo 3: nessuna corrispondenza → crea un nuovo utente (username=email/UPN).
    user = User(
        username=name_id,
        email=name_id,
        password_hash=_NO_LOCAL_PASSWORD,
        role="user",
        saml_entity_id=SAML_IDP_ENTITY_ID,
        saml_name_id=name_id,
        first_name=(attributes.get("givenName") or [None])[0],
        last_name=(attributes.get("surname") or [None])[0],
    )
    db.add(user)
    db.commit()
    logger.info("SAML: creato nuovo utente %s (role=user)", user.username)
    return user


def _ensure_saml_ok(
    db: Session,
    user: User,
    attributes: dict,
    associato: bool,
) -> None:
    """Garantisce che un utente SAML sia coerente.

    Azzera `password_change_required` (l'utente si autentica via SAML/MFA,
    non deve essere bloccato dal cambio password) e aggiorna l'anagrafica
    se gli attributi sono disponibili.
    """
    changed = False
    if user.password_change_required:
        user.password_change_required = False
        changed = True

    given = (attributes.get("givenName") or [None])[0]
    surname = (attributes.get("surname") or [None])[0]
    if given and not user.first_name:
        user.first_name = given
        changed = True
    if surname and not user.last_name:
        user.last_name = surname
        changed = True

    if changed:
        db.commit()