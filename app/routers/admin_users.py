"""Router admin: gestione utenti.

Espone le route amministrative per la gestione degli utenti:
- GET /admin/users              → lista utenti + form creazione
- GET /admin/users/{id}/edit    → pagina di modifica singolo utente
- POST /admin/users/create      → creazione utente (password generata)
- POST /admin/users/{id}/profile → aggiornamento anagrafica
- POST /admin/users/{id}/group  → assegnazione gruppo
- POST /admin/users/{id}/disable → disabilita/abilita
- POST /admin/users/{id}/password → cambio password
- POST /admin/users/{id}/role   → cambio ruolo
- POST /admin/users/{id}/delete → eliminazione definitiva

Protezioni:
- admin non può auto-declassarsi, auto-eliminarsi, né eliminare l'ultimo admin
- eliminazione consentita solo dopo il periodo di grazia da disabilitazione
"""
from __future__ import annotations

import logging
from typing import Annotated
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import TEMPLATES_DIR, USER_DELETE_GRACE_DAYS
from app.core.password import generate_password, hash_password
from app.core.permissions import require_admin
from app.db import get_db
from app.models import Group, User
from app.models.effort_entry import utcnow
from app.schemas.effort import PasswordChange, RoleChange, UserCreate
from app.routers.admin_common import (
    base_context,
    can_delete_user,
    days_since,
    delete_user_records,
    format_last_login,
    user_stats,
)

logger: logging.Logger = logging.getLogger(__name__)

templates: Jinja2Templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

router: APIRouter = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_class=HTMLResponse, name="admin_users")
async def admin_users(
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
    ok: str | None = None,
    err: str | None = None,
    form_ok: str | None = None,
    form_err: str | None = None,
) -> HTMLResponse:
    """Pagina di gestione utenti (lista + form creazione).

    La tabella è di sola visualizzazione: ogni riga ha un pulsante "Modifica"
    che porta alla pagina dedicata `/admin/users/{id}/edit`.
    `ok`/`err` alimentano il banner nella card "Utenti" (operazioni sulla lista);
    `form_ok`/`form_err` alimentano il banner nella card "Nuovo utente" (creazione).
    """
    users = db.execute(
        select(User).where(User.is_superuser.is_(False)).order_by(User.username)
    ).scalars().all()
    groups = db.execute(select(Group).order_by(Group.name)).scalars().all()
    rows = [
        {
            "id": u.id,
            "username": u.username,
            "first_name": u.first_name or "",
            "last_name": u.last_name or "",
            "role": u.role,
            "record_count": user_stats(db, u.id),
            "last_login": format_last_login(u.last_login),
            "disabled": u.disabled,
            "group_name": u.group.name if u.group is not None else "",
        }
        for u in users
    ]
    admin_count = sum(1 for u in users if u.role == "admin")

    ctx = base_context(request, admin.username, "users")
    ctx.update({
        "users": rows,
        "groups": groups,
        "admin_count": admin_count,
        "ok": ok,
        "err": err,
        "form_ok": form_ok,
        "form_err": form_err,
    })
    return templates.TemplateResponse(request=request, name="admin_users.html", context=ctx)


@router.get("/users/{user_id}/edit", response_class=HTMLResponse, name="admin_users_edit")
async def admin_users_edit(
    request: Request,
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
    ok: str | None = None,
    err: str | None = None,
) -> HTMLResponse:
    """Pagina di modifica dedicata per un singolo utente.

    Mostra i dati dell'utente e tutte le azioni di gestione (gruppo, ruolo,
    password, disabilita/abilita, eliminazione) separate dalla lista utenti.
    """
    target = db.get(User, user_id)
    if target is None:
        return RedirectResponse("/admin/users?err=Utente inesistente", status_code=303)
    if target.is_superuser:
        logger.warning("Tentativo di aprire la modifica del superuser (%s)", target.username)
        return RedirectResponse("/admin/users?err=Account di sistema: gestione non disponibile", status_code=303)

    groups = db.execute(select(Group).order_by(Group.name)).scalars().all()
    admin_count = db.execute(
        select(func.count()).select_from(User).where(
            User.role == "admin",
            User.is_superuser.is_(False),
        )
    ).scalar() or 0
    record_count = user_stats(db, target.id)

    user_data = {
        "id": target.id,
        "username": target.username,
        "first_name": target.first_name or "",
        "last_name": target.last_name or "",
        "email": target.email or "",
        "role": target.role,
        "disabled": target.disabled,
        "disabled_at": format_last_login(target.disabled_at),
        "days_since_disabled": days_since(target.disabled_at),
        "can_delete": can_delete_user(target),
        "record_count": record_count,
        "last_login": format_last_login(target.last_login),
        "group_id": target.group_id,
        "group_name": target.group.name if target.group is not None else "",
    }

    ctx = base_context(request, admin.username, "users")
    ctx.update({
        "user": user_data,
        "groups": groups,
        "admin_count": admin_count,
        "is_self": target.id == admin.id,
        "ok": ok,
        "err": err,
    })
    return templates.TemplateResponse(request=request, name="admin_user_edit.html", context=ctx)


@router.post("/users/{user_id}/disable", name="admin_users_disable")
async def admin_users_disable(
    request: Request,
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> RedirectResponse:
    """Disabilita/abilita un utente (blocca il login, record intatti).

    Dopo l'azione torna alla pagina di modifica dell'utente.
    """
    if user_id == admin.id:
        logger.warning("Admin %s tenta di disabilitarsi", admin.username)
        return RedirectResponse(
            f"/admin/users/{user_id}/edit?err=Non puoi disabilitare te stesso",
            status_code=303,
        )

    target = db.get(User, user_id)
    if target is None:
        return RedirectResponse("/admin/users?err=Utente inesistente", status_code=303)
    if target.is_superuser:
        logger.warning("Disabilitazione del superuser bloccata (%s)", target.username)
        return RedirectResponse(
            f"/admin/users/{user_id}/edit?err=Account di sistema: non disabilitabile",
            status_code=303,
        )

    target.disabled = not target.disabled
    # Traccia il momento della disabilitazione (azzerato in riabilitazione).
    target.disabled_at = utcnow() if target.disabled else None
    db.commit()
    stato = "disabilitato" if target.disabled else "riabilitato"
    logger.info("Utente %s %s da admin %s", target.username, stato, admin.username)
    return RedirectResponse(
        f"/admin/users/{user_id}/edit?ok=Utente {stato}", status_code=303
    )


@router.post("/users/create", name="admin_users_create")
async def admin_users_create(
    request: Request,
    username: Annotated[str | None, Form()] = None,
    first_name: Annotated[str | None, Form()] = None,
    last_name: Annotated[str | None, Form()] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> RedirectResponse:
    """Crea un nuovo utente (username email + nome/cognome, ruolo 'user').

    La password viene modificata automaticamente in modo robusto e mostrata
    UNA SOLA volta nel banner di conferma dopo il redirect. Il gruppo non
    viene richiesto in creazione; l'admin lo assegna successivamente dalla
    pagina di modifica utente.

    Nota: usa campi Form() individuali (non Annotated[UserCreate, Form()])
    perché FastAPI non supporta modelli Form() misti ad altri Form() separati.
    Il modello UserCreate viene costruito qui.
    """
    try:
        payload: UserCreate = UserCreate(
            username=username, first_name=first_name, last_name=last_name
        )
    except ValidationError as exc:
        logger.warning("Creazione utente non valida: %s", exc.errors())
        return RedirectResponse("/admin/users?form_err=Dati non validi", status_code=303)

    existing = db.execute(
        select(User).where(User.username == payload.username)
    ).scalar_one_or_none()
    if existing is not None:
        logger.warning("Tentativo di creare utente già esistente %s", payload.username)
        return RedirectResponse("/admin/users?form_err=Username già esistente", status_code=303)

    # Genera una password robusta e la mostra una sola volta nel banner.
    generated_password = generate_password()
    db.add(
        User(
            username=payload.username,
            password_hash=hash_password(generated_password),
            first_name=payload.first_name,
            last_name=payload.last_name,
            email=payload.username,
            role="user",
            group_id=None,
            # La password generata è temporanea: al primo login l'utente è
            # obbligato a cambiarla (password_change_required).
            password_change_required=True,
        )
    )
    db.commit()
    logger.info("Utente creato da admin: %s", payload.username)
    # URL-encode del messaggio: la password generata contiene caratteri
    # speciali (es. &, =, ?) che, non encodati, romperebbero il parametro
    # `form_ok` della query string. FastAPI decodifica il parametro e il
    # banner mostra la password originale. `form_ok`/`form_err` alimentano
    # il banner nella card "Nuovo utente", distinto da `ok`/`err` della lista.
    ok_msg = f"Utente creato. Password temporanea: {generated_password}"
    return RedirectResponse(
        f"/admin/users?{urlencode({'form_ok': ok_msg})}",
        status_code=303,
    )


@router.post("/users/{user_id}/profile", name="admin_users_profile")
async def admin_users_profile(
    request: Request,
    user_id: int,
    username: Annotated[str | None, Form()] = None,
    first_name: Annotated[str | None, Form()] = None,
    last_name: Annotated[str | None, Form()] = None,
    email: Annotated[str | None, Form()] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> RedirectResponse:
    """Aggiorna i dati anagrafici di un utente (username, nome, cognome, email).

    Dopo l'azione torna alla pagina di modifica dell'utente.
    """
    try:
        payload: UserCreate = UserCreate(
            username=username, first_name=first_name, last_name=last_name
        )
    except ValidationError as exc:
        logger.warning("Dati anagrafici non validi per utente id=%s", user_id)
        return RedirectResponse(
            f"/admin/users/{user_id}/edit?err=Dati non validi", status_code=303
        )

    target = db.get(User, user_id)
    if target is None:
        return RedirectResponse("/admin/users?err=Utente inesistente", status_code=303)
    if target.is_superuser:
        logger.warning("Modifica anagrafica del superuser bloccata (%s)", target.username)
        return RedirectResponse(
            f"/admin/users/{user_id}/edit?err=Account di sistema: dati non modificabili",
            status_code=303,
        )

    # Eventuale email distinta dall'username (se non fornita, usa l'username).
    stripped_email = (email or "").strip()
    new_email = stripped_email if stripped_email else payload.username

    # Controllo duplicazione username (escluso l'utente stesso).
    existing = db.execute(
        select(User).where(User.username == payload.username, User.id != user_id)
    ).scalar_one_or_none()
    if existing is not None:
        logger.warning("Tentativo di usare username già esistente %s", payload.username)
        return RedirectResponse(
            f"/admin/users/{user_id}/edit?err=Username già esistente", status_code=303
        )

    target.username = payload.username
    target.first_name = payload.first_name
    target.last_name = payload.last_name
    target.email = new_email
    db.commit()
    logger.info("Dati anagrafici aggiornati per %s da admin", target.username)
    return RedirectResponse(
        f"/admin/users/{user_id}/edit?ok=Dati anagrafici aggiornati", status_code=303
    )


@router.post("/users/{user_id}/group", name="admin_users_group")
async def admin_users_group(
    request: Request,
    user_id: int,
    group_id: Annotated[int | None, Form()] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> RedirectResponse:
    """Assegna il gruppo di appartenenza a un utente.

    Dopo l'azione torna alla pagina di modifica dell'utente.
    """
    target = db.get(User, user_id)
    if target is None:
        return RedirectResponse("/admin/users?err=Utente inesistente", status_code=303)
    if target.is_superuser:
        logger.warning("Assegnazione gruppo al superuser bloccata (%s)", target.username)
        return RedirectResponse(
            f"/admin/users/{user_id}/edit?err=Account di sistema: gruppo non assegnabile",
            status_code=303,
        )
    if group_id is not None:
        group = db.get(Group, group_id)
        if group is None:
            return RedirectResponse(
                f"/admin/users/{user_id}/edit?err=Gruppo inesistente", status_code=303
            )
    target.group_id = group_id
    db.commit()
    logger.info("Gruppo assegnato all'utente %s: %s", target.username, group_id)
    return RedirectResponse(
        f"/admin/users/{user_id}/edit?ok=Gruppo aggiornato", status_code=303
    )


@router.post("/users/{user_id}/password", name="admin_users_password")
async def admin_users_password(
    request: Request,
    user_id: int,
    password: Annotated[PasswordChange, Form()],
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> RedirectResponse:
    """Cambia la password di un utente.

    Dopo l'azione torna alla pagina di modifica dell'utente.
    """
    try:
        payload: PasswordChange = PasswordChange(**password.model_dump())
    except ValidationError as exc:
        logger.warning("Cambio password non valido per utente id=%s", user_id)
        return RedirectResponse(
            f"/admin/users/{user_id}/edit?err=Password non valida", status_code=303
        )

    target = db.get(User, user_id)
    if target is None:
        return RedirectResponse("/admin/users?err=Utente inesistente", status_code=303)
    if target.is_superuser:
        logger.warning("Cambio password del superuser bloccato (%s)", target.username)
        return RedirectResponse(
            f"/admin/users/{user_id}/edit?err=Account di sistema: password via /profile",
            status_code=303,
        )
    target.password_hash = hash_password(payload.password)
    db.commit()
    logger.info("Password cambiata per %s da admin", target.username)
    return RedirectResponse(
        f"/admin/users/{user_id}/edit?ok=Password aggiornata", status_code=303
    )


@router.post("/users/{user_id}/role", name="admin_users_role")
async def admin_users_role(
    request: Request,
    user_id: int,
    role: Annotated[RoleChange, Form()],
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> RedirectResponse:
    """Cambia il ruolo di un utente (blocca l'auto-declassamento).

    Dopo l'azione torna alla pagina di modifica dell'utente.
    """
    try:
        payload: RoleChange = RoleChange(**role.model_dump())
    except ValidationError as exc:
        logger.warning("Cambio ruolo non valido: %s", exc.errors())
        return RedirectResponse(
            f"/admin/users/{user_id}/edit?err=Ruolo non valido", status_code=303
        )

    if user_id == admin.id:
        logger.warning("Admin %s tenta di auto-declassarsi", admin.username)
        return RedirectResponse(
            f"/admin/users/{user_id}/edit?err=Non puoi cambiare il tuo ruolo",
            status_code=303,
        )

    target = db.get(User, user_id)
    if target is None:
        return RedirectResponse("/admin/users?err=Utente inesistente", status_code=303)
    if target.is_superuser:
        logger.warning("Cambio ruolo del superuser bloccato (%s)", target.username)
        return RedirectResponse(
            f"/admin/users/{user_id}/edit?err=Account di sistema: ruolo non modificabile",
            status_code=303,
        )
    target.role = payload.role
    db.commit()
    logger.info("Ruolo di %s cambiato in %s", target.username, payload.role)
    return RedirectResponse(
        f"/admin/users/{user_id}/edit?ok=Ruolo aggiornato", status_code=303
    )


@router.post("/users/{user_id}/delete", name="admin_users_delete")
async def admin_users_delete(
    request: Request,
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> RedirectResponse:
    """Elimina un utente (blocca auto-eliminazione e ultimo admin).

    Dopo l'eliminazione riuscita torna alla lista utenti (l'utente non esiste
    più); negli errori bloccanti resta sulla pagina di modifica dell'utente.
    """
    if user_id == admin.id:
        logger.warning("Admin %s tenta di auto-eliminarsi", admin.username)
        return RedirectResponse(
            f"/admin/users/{user_id}/edit?err=Non puoi eliminare te stesso", status_code=303
        )

    target = db.get(User, user_id)
    if target is None:
        return RedirectResponse("/admin/users?err=Utente inesistente", status_code=303)
    if target.is_superuser:
        logger.warning("Eliminazione del superuser bloccata (%s)", target.username)
        return RedirectResponse(
            f"/admin/users/{user_id}/edit?err=Account di sistema: non eliminabile",
            status_code=303,
        )

    if target.role == "admin":
        admin_count = db.execute(
            select(func.count()).select_from(User).where(
                User.role == "admin",
                User.is_superuser.is_(False),
            )
        ).scalar() or 0
        if admin_count <= 1:
            logger.warning("Tentativo di eliminare l'ultimo admin (%s)", target.username)
            return RedirectResponse(
                f"/admin/users/{user_id}/edit?err=Non puoi eliminare l'ultimo admin",
                status_code=303,
            )

    # Finestra temporale minima dopo la disabilitazione.
    if not can_delete_user(target):
        giorni = days_since(target.disabled_at) or 0
        logger.warning(
            "Eliminazione utente %s bloccata: disabilitato da %d/%d giorni",
            target.username,
            giorni,
            USER_DELETE_GRACE_DAYS,
        )
        return RedirectResponse(
            f"/admin/users/{user_id}/edit?err=Eliminazione consentita dopo almeno "
            f"{USER_DELETE_GRACE_DAYS} giorni dalla disabilitazione (trascorsi {giorni})",
            status_code=303,
        )

    # Elimina definitivamente anche i record dell'utente.
    rimossi = delete_user_records(db, target.id)
    db.delete(target)
    db.commit()
    logger.info(
        "Utente eliminato da admin: %s (record eliminati: %d)",
        target.username,
        rimossi,
    )
    return RedirectResponse(f"/admin/users?ok=Utente eliminato ({rimossi} record rimossi)", status_code=303)