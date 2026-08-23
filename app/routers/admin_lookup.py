"""Router admin: gestione lookup (clienti, gruppi, attività).

Espone le route amministrative per la gestione delle tabelle lookup:
- GET /admin/lookup                  → pagina di gestione (schedario)
- POST /admin/lookup/create          → aggiunge una voce
- POST /admin/lookup/{id}/edit       → rinomina una voce
- POST /admin/lookup/{id}/delete     → elimina una voce (bloccato se in uso)

La voce sentinella "NON LAVORATO" (S6) non è creabile via UI, non è
rinominabile né eliminabile: è gestita esclusivamente dal seed.
"""
from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import TEMPLATES_DIR
from app.core.permissions import require_admin
from app.core.seed import SENTINEL_NAME
from app.db import get_db
from app.models import Activity, Client, EffortEntry, Group, User
from app.routers.admin_common import base_context, lookup_model
from app.schemas.effort import LookupCreate

logger: logging.Logger = logging.getLogger(__name__)

templates: Jinja2Templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

router: APIRouter = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/lookup", response_class=HTMLResponse, name="admin_lookup")
async def admin_lookup(
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
    ok: str | None = None,
    err: str | None = None,
) -> HTMLResponse:
    """Pagina di gestione lookup: clienti, gruppi, attività."""
    clients = db.execute(select(Client).order_by(Client.name)).scalars().all()
    groups = db.execute(select(Group).order_by(Group.name)).scalars().all()
    activities = db.execute(select(Activity).order_by(Activity.name)).scalars().all()

    # Conta i record associati a ciascun lookup (per bloccare l'eliminazione).
    used_client_ids = set(
        db.execute(select(EffortEntry.client_id).distinct()).scalars().all()
    )
    used_group_ids = set(
        db.execute(select(EffortEntry.group_id).distinct()).scalars().all()
    )
    used_activity_ids = set(
        db.execute(select(EffortEntry.activity_id).distinct()).scalars().all()
    )

    ctx = base_context(request, admin.username, "lookup")
    ctx.update({
        "clients": clients,
        "groups": groups,
        "activities": activities,
        "used_client_ids": used_client_ids,
        "used_group_ids": used_group_ids,
        "used_activity_ids": used_activity_ids,
        "ok": ok,
        "err": err,
    })
    return templates.TemplateResponse(request=request, name="admin_lookup.html", context=ctx)


@router.post("/lookup/create", name="admin_lookup_create")
async def admin_lookup_create(
    request: Request,
    lookup: Annotated[LookupCreate, Form()],
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> RedirectResponse:
    """Aggiunge una voce lookup."""
    try:
        payload: LookupCreate = LookupCreate(**lookup.model_dump())
    except ValidationError as exc:
        logger.warning("Creazione lookup non valida: %s", exc.errors())
        return RedirectResponse("/admin/lookup?err=Dati non validi", status_code=303)

    # La voce sentinella "NON LAVORATO" (S6) non può essere creata via UI:
    # è gestita esclusivamente dal seed. Evita collisioni col meccanismo giorni
    # non lavorati.
    if payload.name.upper() == SENTINEL_NAME:
        logger.warning("Creazione lookup '%s' bloccata (sentinella)", payload.name)
        return RedirectResponse(
            "/admin/lookup?err=Nome riservato", status_code=303
        )

    model = lookup_model(payload.type)
    existing = db.execute(
        select(model).where(model.name == payload.name)
    ).scalar_one_or_none()
    if existing is not None:
        return RedirectResponse("/admin/lookup?err=Nome già esistente", status_code=303)

    db.add(model(name=payload.name))
    db.commit()
    logger.info("Lookup %s creato: %s", payload.type, payload.name)
    return RedirectResponse("/admin/lookup?ok=Elemento aggiunto", status_code=303)


@router.post("/lookup/{lookup_id}/edit", name="admin_lookup_edit")
async def admin_lookup_edit(
    request: Request,
    lookup_id: int,
    lookup_type: Annotated[str, Form()],
    name: Annotated[str, Form()],
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> RedirectResponse:
    """Modifica il nome di una voce lookup."""
    try:
        payload: LookupCreate = LookupCreate(type=lookup_type, name=name)
    except ValidationError as exc:
        logger.warning("Modifica lookup non valida: %s", exc.errors())
        return RedirectResponse("/admin/lookup?err=Nome non valido", status_code=303)

    model = lookup_model(payload.type)
    target = db.get(model, lookup_id)
    if target is None:
        return RedirectResponse("/admin/lookup?err=Elemento inesistente", status_code=303)

    # La voce sentinella "NON LAVORATO" non è rinominabile: è un meccanismo
    # interno usato per i giorni non lavorati (S6). Rinomarla romperebbe
    # l'allineamento dell'app con il nome sentinella.
    if target.name.upper() == SENTINEL_NAME:
        logger.warning("Rinomina lookup sentinella '%s' bloccata", target.name)
        return RedirectResponse(
            "/admin/lookup?err=Elemento sentinella non modificabile", status_code=303
        )

    target.name = payload.name
    db.commit()
    logger.info("Lookup %s id=%s rinominato in %s", payload.type, lookup_id, payload.name)
    return RedirectResponse("/admin/lookup?ok=Elemento aggiornato", status_code=303)


@router.post("/lookup/{lookup_id}/delete", name="admin_lookup_delete")
async def admin_lookup_delete(
    request: Request,
    lookup_id: int,
    lookup_type: Annotated[str, Form()],
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> RedirectResponse:
    """Elimina una voce lookup (bloccato se ha record associati)."""
    try:
        model = lookup_model(lookup_type)
    except ValueError as exc:
        return RedirectResponse("/admin/lookup?err=Tipo non valido", status_code=303)

    target = db.get(model, lookup_id)
    if target is None:
        return RedirectResponse("/admin/lookup?err=Elemento inesistente", status_code=303)

    # La voce sentinella "NON LAVORATO" non è eliminabile: è un meccanismo
    # interno (S6). Protezione esplicita, oltre al blocco per record associati.
    if target.name.upper() == SENTINEL_NAME:
        logger.warning("Eliminazione lookup sentinella '%s' bloccata", target.name)
        return RedirectResponse(
            "/admin/lookup?err=Elemento sentinella non eliminabile", status_code=303
        )

    # Colonna FK che collega il lookup a effort_entries.
    fk_col = {
        Client: EffortEntry.client_id,
        Group: EffortEntry.group_id,
        Activity: EffortEntry.activity_id,
    }[model]

    associated = db.execute(
        select(func.count()).select_from(EffortEntry).where(fk_col == lookup_id)
    ).scalar() or 0
    if associated > 0:
        logger.warning(
            "Eliminazione lookup %s id=%s bloccata: %d record associati",
            lookup_type,
            lookup_id,
            associated,
        )
        return RedirectResponse("/admin/lookup?err=Elemento con record associati", status_code=303)

    db.delete(target)
    db.commit()
    logger.info("Lookup %s id=%s eliminato", lookup_type, lookup_id)
    return RedirectResponse("/admin/lookup?ok=Elemento eliminato", status_code=303)