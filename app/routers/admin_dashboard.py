"""Router admin: dashboard e registrazioni globali.

Espone le route amministrative relative al pannello di controllo e
all'elenco/export di TUTTI i record del sistema:
- GET /admin            → dashboard di benvenuto (KPI e metriche)
- GET /admin/records    → tabella di tutti i record (no form, con filtro anno/mese)
- GET /admin/records/export → export CSV/XLSX di tutti i record

Tutte le route sono protette da `require_admin`.
"""
from __future__ import annotations

import logging
from datetime import date

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.config import TEMPLATES_DIR
from app.core.permissions import require_admin
from app.db import get_db
from app.models import EffortEntry, Group, User
from app.routers.web import _resolve_month
from app.services.export_csv import MESI_ITALIANI, build_csv
from app.services.export_xlsx import XLSX_MEDIA_TYPE, build_xlsx
from app.routers.admin_common import (
    base_context,
    db_size_mb,
    inactive_users,
    month_bounds,
    users_without_group,
)
from fastapi.templating import Jinja2Templates

logger: logging.Logger = logging.getLogger(__name__)

templates: Jinja2Templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

router: APIRouter = APIRouter(prefix="/admin", tags=["admin"])


@router.get("", response_class=HTMLResponse, name="admin_dashboard")
async def admin_dashboard(
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> HTMLResponse:
    """Dashboard admin con KPI e metriche di sistema."""
    today = date.today()
    m_start, m_end = month_bounds()

    # --- KPI base -----------------------------------------------------------
    total_users = db.execute(
        select(func.count()).select_from(User).where(User.is_superuser.is_(False))
    ).scalar() or 0
    active_users = db.execute(
        select(func.count()).select_from(User).where(
            User.disabled.is_(False),
            User.is_superuser.is_(False),
        )
    ).scalar() or 0
    disabled_users = total_users - active_users
    total_records = db.execute(
        select(func.count()).select_from(EffortEntry)
    ).scalar() or 0

    hours_month = db.execute(
        select(func.coalesce(func.sum(EffortEntry.hours_spent), 0)).where(
            EffortEntry.work_date >= m_start,
            EffortEntry.work_date <= m_end,
        )
    ).scalar() or 0
    records_today = db.execute(
        select(func.count()).select_from(EffortEntry).where(
            EffortEntry.work_date == today
        )
    ).scalar() or 0

    # --- Distribuzione per gruppo (utenti + ore del mese) ------------------
    group_rows = []
    for g in db.execute(select(Group).order_by(Group.name)).scalars().all():
        user_count = db.execute(
            select(func.count()).select_from(User).where(
                User.group_id == g.id,
                User.disabled.is_(False),
                User.is_superuser.is_(False),
            )
        ).scalar() or 0
        hours = db.execute(
            select(func.coalesce(func.sum(EffortEntry.hours_spent), 0)).where(
                EffortEntry.group_id == g.id,
                EffortEntry.work_date >= m_start,
                EffortEntry.work_date <= m_end,
            )
        ).scalar() or 0
        group_rows.append({"name": g.name, "users": user_count, "hours": float(hours)})

    # --- Ultima attività ------------------------------------------------------
    recent_records = (
        db.execute(
            select(EffortEntry)
            .options(
                selectinload(EffortEntry.client),
                selectinload(EffortEntry.group),
                selectinload(EffortEntry.activity),
                selectinload(EffortEntry.user),
            )
            .order_by(EffortEntry.work_date.desc(), EffortEntry.created_at.desc())
            .limit(20)
        )
        .scalars()
        .all()
    )
    last_record = recent_records[0] if recent_records else None

    ctx = base_context(request, admin.username, "dashboard")
    ctx.update({
        "kpi": {
            "total_users": total_users,
            "active_users": active_users,
            "disabled_users": disabled_users,
            "total_records": total_records,
            "hours_month": hours_month,
            "records_today": records_today,
        },
        "group_stats": group_rows,
        "inactive_users": inactive_users(db, days=7),
        "users_without_group": users_without_group(db),
        "recent_records": recent_records,
        "last_record": last_record,
        "month_label": f"{MESI_ITALIANI[today.month]} {today.year}",
        "db_size": db_size_mb(),
    })
    return templates.TemplateResponse(
        request=request,
        name="admin_dashboard.html",
        context=ctx,
    )


@router.get("/records", response_class=HTMLResponse, name="admin_records")
async def admin_records(
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
    month: str | None = None,
    year: str | None = None,
    month_num: str | None = None,
) -> HTMLResponse:
    """Tabella di tutti i record del sistema (no form, con filtro anno/mese)."""
    filter_month = _resolve_month(year, month_num, month)

    # Anni distinti presenti (ordinati desc).
    year_stmt = (
        select(func.strftime("%Y", EffortEntry.work_date).label("year"))
        .distinct()
        .order_by(func.strftime("%Y", EffortEntry.work_date).desc())
    )
    year_options = db.execute(year_stmt).scalars().all()

    stmt = (
        select(EffortEntry)
        .options(
            selectinload(EffortEntry.client),
            selectinload(EffortEntry.group),
            selectinload(EffortEntry.activity),
            selectinload(EffortEntry.user),
        )
        .order_by(EffortEntry.work_date.desc())
    )
    if filter_month:
        stmt = stmt.where(func.strftime("%Y-%m", EffortEntry.work_date) == filter_month)
    records = db.execute(stmt).scalars().all()

    selected_year: str = ""
    selected_month_num: str = ""
    if filter_month and len(filter_month) == 7:
        y, m = filter_month.split("-")
        selected_year = y
        selected_month_num = m

    ctx = base_context(request, admin.username, "records")
    ctx.update({
        "records": records,
        "year_options": year_options,
        "month_options": MESI_ITALIANI,
        "selected_year": selected_year,
        "selected_month_num": selected_month_num,
    })
    return templates.TemplateResponse(
        request=request,
        name="admin_records.html",
        context=ctx,
    )


@router.get("/records/export", response_class=StreamingResponse, name="admin_records_export")
async def admin_records_export(
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
    month: str | None = None,
    year: str | None = None,
    month_num: str | None = None,
    format: str | None = None,
) -> StreamingResponse:
    """Esporta in CSV o XLSX tutti i record del sistema (solo admin)."""
    filter_month = _resolve_month(year, month_num, month)

    stmt = (
        select(EffortEntry)
        .options(
            selectinload(EffortEntry.client),
            selectinload(EffortEntry.group),
            selectinload(EffortEntry.activity),
            selectinload(EffortEntry.user),
        )
        .order_by(EffortEntry.work_date.asc())
    )
    if filter_month:
        stmt = stmt.where(func.strftime("%Y-%m", EffortEntry.work_date) == filter_month)
    records = db.execute(stmt).scalars().all()

    base_name = f"effort_admin_{filter_month or 'tutti'}"
    if format == "xlsx":
        logger.info("Export XLSX admin (record=%d, mese=%s)", len(records), filter_month or "tutti")
        return StreamingResponse(
            iter([build_xlsx(records)]),
            media_type=XLSX_MEDIA_TYPE,
            headers={"Content-Disposition": f'attachment; filename="{base_name}.xlsx"'},
        )
    logger.info("Export CSV admin (record=%d, mese=%s)", len(records), filter_month or "tutti")
    return StreamingResponse(
        iter([build_csv(records)]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{base_name}.csv"'},
    )