"""Router web dell'applicazione Effort Tracking.

Espone le pagine HTML renderizzate server-side con Jinja2 e gli endpoint
di base (indice, health check). Le route business sono protette: se
l'autenticazione è attiva e non c'è una sessione valida, l'utente viene
rediretto al login.

Ogni utente normale vede, crea, modifica ed esporta solo i propri record;
l'admin (ruolo "admin") vede tutti i record come supervisore. `user_id`
viene valorizzato su ogni nuovo record con l'utente della sessione.
"""
from __future__ import annotations

import csv
import io
import logging
from datetime import date, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, StreamingResponse
from pydantic import ValidationError
from sqlalchemy import Select, func, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, selectinload
from fastapi.templating import Jinja2Templates

from app.config import APP_NAME, APP_VERSION, AUTH_ENABLED, TEMPLATES_DIR
from app.core.permissions import is_admin, is_manager
from app.core.seed import SENTINEL_NAME
from app.db import get_db
from app.dependencies import get_current_user
from app.models import Activity, Client, EffortEntry, Group, User
from app.schemas.effort import EffortEntryCreate

logger: logging.Logger = logging.getLogger(__name__)

# Template engine condiviso dal router web.
templates: Jinja2Templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


router: APIRouter = APIRouter(tags=["web"])

# Nomi dei mesi in italiano (indice 0 vuoto, 1..12).
_MESI_ITALIANI = [
    "", "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
    "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre",
]

# Header del CSV di export, coerente con le colonne della tabella.
_CSV_HEADER = [
    "Data",
    "Cliente",
    "Gruppo",
    "Attività",
    "Utente",
    "Ore",
    "Note",
    "Descrizione attività",
]


def _require_auth(user: User | None) -> RedirectResponse | None:
    """Se l'auth è attiva e manca l'utente, restituisce il redirect al login."""
    if AUTH_ENABLED and user is None:
        return RedirectResponse("/login", status_code=303)
    return None


def _filter_by_user(stmt: Select, user: User) -> Select:
    """Filtra una query sugli effort in base al ruolo.

    L'admin vede tutti i record; un utente normale solo i propri.
    """
    if is_admin(user):
        return stmt
    return stmt.where(EffortEntry.user_id == user.id)


def _resolve_month(
    year: str | None, month_num: str | None, month: str | None = None
) -> str | None:
    """Deriva il filtro mese in formato `YYYY-MM` da anno + mese separati.

    Priorità: 1) `month` esplicito (retrocompatibilità con URL/form vecchi
    che passavano già `YYYY-MM`); 2) `year` + `month_num` (nuovo filtro S4).
    Ritorna `None` se non c'è un filtro valido.

    Parametri:
        year: anno (4 cifre) o None.
        month_num: numero mese (1-12) o None.
        month: valore legacy `YYYY-MM` (opzionale, fallback).

    Ritorna:
        La stringa `YYYY-MM` da usare nel filtro, oppure None.
    """
    if month and month != "None":  # "None" (stringa) = mese non valido
        return month
    if year and month_num:
        try:
            y = int(year)
            m = int(month_num)
            if 1 <= m <= 12:
                return f"{y:04d}-{m:02d}"
        except (TypeError, ValueError):
            return None
    return None


def _with_month(base_url: str, filter_month: str | None) -> str:
    """Aggiunge i parametri anno/mese a un URL se il filtro è attivo.

    Riceve un filtro in formato `YYYY-MM` (già risolto) e lo converte in
    `?year=YYYY&month_num=MM` per coerenza col nuovo filtro S4.

    Parametri:
        base_url: URL di base.
        filter_month: filtro `YYYY-MM` (None se non filtrato).

    Ritorna:
        L'URL con `?year=...&month_num=...` se il filtro è attivo, altrimenti
        l'URL di partenza.
    """
    if filter_month and filter_month != "None":  # "None" = mese non valido
        if len(filter_month) == 7 and filter_month[4] == "-":
            year, month_num = filter_month.split("-")
        else:
            return base_url
        separator: str = "&" if "?" in base_url else "?"
        return f"{base_url}{separator}year={year}&month_num={month_num}"
    return base_url


def _sidebar_items(user: User) -> list[dict[str, str]]:
    """Voci della sidebar in base al ruolo dell'utente loggato.

    - USER: "Registrazioni" + "Profilo".
    - MANAGER: "Registrazioni" + "Gruppo" (vista gruppo) + "Profilo".
    - ADMIN: Dashboard + Registrazioni + Gestione Utenti + Gestione Lookup
      (il Profilo è accessibile dal menu utente, non dalla sidebar admin).
    """
    if is_admin(user):
        return [
            {"label": "Dashboard", "href": "/admin"},
            {"label": "Registrazioni", "href": "/admin/records"},
            {"label": "Gestione Utenti", "href": "/admin/users"},
            {"label": "Gestione Lookup", "href": "/admin/lookup"},
        ]
    items: list[dict[str, str]] = [
        {"label": "Registrazioni", "href": "/"},
    ]
    if is_manager(user):
        items.append({"label": "Gruppo", "href": "/group"})
    items.append({"label": "Profilo", "href": "/profile"})
    return items


@router.get("/", response_class=HTMLResponse, name="index")
async def index(
    request: Request,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
    success: int | None = None,
    error: str | None = None,
    month: str | None = None,
    year: str | None = None,
    month_num: str | None = None,
    highlight_id: int | None = None,
) -> HTMLResponse:
    """Pagina principale: form di inserimento + tabella elenco (protetta)."""
    redirect = _require_auth(user)
    if redirect is not None:
        return redirect
    assert user is not None  # con auth attiva, dopo _require_auth l'utente c'è.

    # L'admin atterra sulla dashboard /admin, non sulla pagina di
    # registrazione (che non può usare: niente card form, solo consultazione).
    if is_admin(user):
        return RedirectResponse("/admin", status_code=303)

    clients = db.execute(select(Client).order_by(Client.name)).scalars().all()
    activities = db.execute(select(Activity).order_by(Activity.name)).scalars().all()

    # Gruppo di appartenenza: non un select, ma un campo readonly
    # autopopolato come User.
    current_group_name: str = ""
    current_group_id: int | None = None
    if user.group_id is not None:
        group = db.get(Group, user.group_id)
        if group is not None:
            current_group_name = group.name
            current_group_id = group.id

    # Filtro mese risolto da anno + mese separati (S4), con fallback sul
    # vecchio parametro `month` per retrocompatibilità.
    filter_month = _resolve_month(year, month_num, month)

    # Anni distinti limitati ai record visibili all'utente (ordinati desc).
    year_stmt = (
        select(func.strftime("%Y", EffortEntry.work_date).label("year"))
        .distinct()
        .order_by(func.strftime("%Y", EffortEntry.work_date).desc())
    )
    year_stmt = _filter_by_user(year_stmt, user)
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
    stmt = _filter_by_user(stmt, user)
    if filter_month:
        stmt = stmt.where(func.strftime("%Y-%m", EffortEntry.work_date) == filter_month)
    records = db.execute(stmt).scalars().all()

    success_message: str | None = None
    if success == 1:
        success_message = "Record salvato correttamente."
    elif success == 2:
        success_message = "Registrazione aggiornata correttamente."
    elif success == 3:
        success_message = "Registrazione eliminata correttamente."

    current_username: str = user.username

    # Nome e cognome per il campo User readonly del form (visualizzazione).
    current_full_name: str = user.full_name

    # Anno e mese selezionati per i dropdown (per riempire i `selected`).
    selected_year: str = ""
    selected_month_num: str = ""
    if filter_month and len(filter_month) == 7:
        y, m = filter_month.split("-")
        selected_year = y
        selected_month_num = m

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "app_name": APP_NAME,
            "app_version": APP_VERSION,
            "phase": "Registrazioni",
            "clients": clients,
            "activities": activities,
            "current_group_name": current_group_name,
            "current_group_id": current_group_id,
            "records": records,
            "year_options": year_options,
            "month_options": _MESI_ITALIANI,  # indice 0 vuoto, 1..12
            "selected_year": selected_year,
            "selected_month_num": selected_month_num,
            "today": date.today().isoformat(),
            "success_message": success_message,
            "error": error,
            "current_username": current_username,
            "current_full_name": current_full_name,
            "auth_enabled": AUTH_ENABLED,
            "is_admin": is_admin(user),
            "sidebar_items": _sidebar_items(user),
            # Id del record da evidenziare dopo l'aggiornamento.
            "highlight_id": highlight_id,
        },
    )


@router.post("/", response_class=HTMLResponse, name="save_entry")
async def save_entry(
    request: Request,
    user: Annotated[str | None, Form()] = None,
    date: Annotated[date | None, Form()] = None,
    client_id: Annotated[int | None, Form()] = None,
    group_id: Annotated[int | None, Form()] = None,
    activity_id: Annotated[int | None, Form()] = None,
    hours: Annotated[float | None, Form()] = None,
    notes: Annotated[str | None, Form()] = None,
    description: Annotated[str | None, Form()] = None,
    action: Annotated[str, Form()] = "single",
    record_id: Annotated[int | None, Form()] = None,
    month: Annotated[str | None, Form()] = None,
    year: Annotated[str | None, Form()] = None,
    month_num: Annotated[str | None, Form()] = None,
    is_holiday: Annotated[bool, Form()] = False,
    current_user: User | None = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    """Salva o aggiorna un record di effort (protetta).

    Con auth attiva, il campo User viene forzato lato server allo username
    della sessione, indipendentemente da quanto inviato dal browser.
    `month`/`year`/`month_num` preservano il filtro mese/anno nel redirect.
    `user_id` viene valorizzato con l'utente della sessione.
    """
    redirect = _require_auth(current_user)
    if redirect is not None:
        return redirect
    assert current_user is not None

    # Filtro mese risolto da anno + mese separati (S4), con fallback sul
    # vecchio parametro `month` per retrocompatibilità.
    filter_month = _resolve_month(year, month_num, month)

    # Con auth attiva, rispetta sempre l'utente della sessione (il campo
    # User è readonly lato client, ma qui se ne garantisce l'integrità).
    # Anche il Gruppo viene forzato al gruppo di appartenenza dell'utente
    # di sessione, ignorando il valore inviato dal browser.
    if AUTH_ENABLED:
        user = current_user.username
        group_id = current_user.group_id

    # Eliminazione definitiva: richiede solo `record_id`.
    if action == "delete":
        return _delete_entry(record_id, db, current_user, filter_month)

    try:
        payload = EffortEntryCreate(
            user=user,
            date=date,
            client_id=client_id,
            group_id=group_id,
            activity_id=activity_id,
            hours=hours,
            notes=notes,
            description=description,
            is_holiday=is_holiday,
        )
    except ValidationError as exc:
        logger.warning("Validazione fallita nel form: %s", exc.errors())
        return RedirectResponse(_with_month("/?error=validazione", filter_month), status_code=303)

    # Giorno non lavorato (S6): forza i valori sentinella lato server.
    # Cliente e Attività vengono impostati ai lookup "NON LAVORATO",
    # le ore a 8.0 e le note a "NON LAVORATO". Il gruppo resta quello di
    # sessione (già forzato sopra quando AUTH_ENABLED).
    if payload.is_holiday:
        payload = _force_holiday_values(payload, db)
        if payload is None:
            logger.warning("Lookup sentinella NON LAVORATO assenti nel DB")
            return RedirectResponse(_with_month("/?error=validazione", filter_month), status_code=303)

    activity = db.execute(
        select(Activity).where(Activity.id == payload.activity_id)
    ).scalar_one_or_none()

    if activity is not None and activity.requires_description and not payload.description:
        logger.warning("Descrizione mancante per attività che la richiede")
        return RedirectResponse(_with_month("/?error=descrizione", filter_month), status_code=303)

    if action == "week" and record_id is not None:
        return RedirectResponse(_with_month("/?error=validazione", filter_month), status_code=303)

    if action == "week":
        return _save_week(payload, db, current_user, filter_month)

    return _save_single(payload, db, current_user, record_id=record_id, month=filter_month)


def _force_holiday_values(
    payload: EffortEntryCreate, db: Session
) -> EffortEntryCreate | None:
    """Forza i valori sentinella per un giorno non lavorato (S6).

    Recupera i lookup "NON LAVORATO" per Cliente e Attività e imposta
    `client_id`, `activity_id`, `hours=8.0` e `notes`. Ritorna `None` se
    i lookup sentinella non esistono nel DB (seed non eseguito).
    """
    client = db.execute(
        select(Client).where(Client.name == SENTINEL_NAME)
    ).scalar_one_or_none()
    activity = db.execute(
        select(Activity).where(Activity.name == SENTINEL_NAME)
    ).scalar_one_or_none()
    if client is None or activity is None:
        return None

    # Nota: group_id resta quello di sessione (forzato in save_entry).
    payload.client_id = client.id
    payload.activity_id = activity.id
    payload.hours = 8.0
    payload.notes = SENTINEL_NAME
    payload.description = None
    return payload


def _is_sentinel_entry(record: EffortEntry) -> bool:
    """True se il record è un giorno non lavorato (cliente sentinella)."""
    return record.client is not None and record.client.name == SENTINEL_NAME


def _delete_entry(
    record_id: int | None,
    db: Session,
    current_user: User,
    month: str | None = None,
) -> RedirectResponse:
    """Elimina definitivamente un record di effort dal database.

    Ogni utente può eliminare SOLO i propri record. Nessuna eccezione per
    admin/manager — la modifica o cancellazione di record altrui non è mai
    consentita (regola aziendale: nessuno tocca i dati degli altri, nemmeno
    con ruolo di supervisione).
    """
    if record_id is None:
        logger.warning("Eliminazione senza record_id")
        return RedirectResponse(_with_month("/?error=validazione", month), status_code=303)

    entry = db.get(EffortEntry, record_id)
    if entry is None:
        logger.warning("Tentativo di eliminazione record inesistente id=%s", record_id)
        return RedirectResponse(_with_month("/?error=validazione", month), status_code=303)

    if entry.user_id != current_user.id:
        logger.warning(
            "Utente %s tenta di eliminare record altrui id=%s",
            current_user.username,
            record_id,
        )
        return RedirectResponse(_with_month("/?error=validazione", month), status_code=303)

    db.delete(entry)
    db.commit()
    logger.info("Record eliminato id=%s", record_id)
    return RedirectResponse(_with_month("/?success=3", month), status_code=303)


def _save_single(
    payload: EffortEntryCreate,
    db: Session,
    current_user: User,
    record_id: int | None = None,
    month: str | None = None,
) -> RedirectResponse:
    """Crea un nuovo record oppure aggiorna quello indicato da `record_id`.

    Il nuovo record viene associato all'utente corrente; su update ogni
    utente può modificare SOLO i propri record (nessuna eccezione per
    admin/manager — regola aziendale).
    """
    if record_id is not None:
        entry = db.get(EffortEntry, record_id)
        if entry is None:
            logger.warning("Update di record inesistente id=%s", record_id)
            return RedirectResponse(_with_month("/?error=validazione", month), status_code=303)
        # Ogni utente può aggiornare SOLO i propri record. Nessuna eccezione
        # per admin/manager (regola aziendale).
        if entry.user_id != current_user.id:
            logger.warning(
                "Utente %s tenta di aggiornare record altrui id=%s",
                current_user.username,
                record_id,
            )
            return RedirectResponse(_with_month("/?error=validazione", month), status_code=303)
        # Su update il proprietario del record non cambia (è sempre l'utente
        # corrente, già verificato sopra).
        entry.client_id = payload.client_id
        entry.group_id = payload.group_id
        entry.activity_id = payload.activity_id
        entry.work_date = payload.date
        entry.hours_spent = payload.hours
        entry.notes = payload.notes
        entry.description = payload.description
        db.commit()
        logger.info("Record aggiornato id=%s data=%s ore=%s", record_id, payload.date, payload.hours)
        # Passa l'id del record per evidenziarlo nella tabella.
        base = f"/?success=2&highlight_id={record_id}"
        return RedirectResponse(_with_month(base, month), status_code=303)

    entry = EffortEntry(
        user_id=current_user.id,
        client_id=payload.client_id,
        group_id=payload.group_id,
        activity_id=payload.activity_id,
        work_date=payload.date,
        hours_spent=payload.hours,
        notes=payload.notes,
        description=payload.description,
    )
    db.add(entry)
    db.commit()
    logger.info("Record creato id=%s data=%s ore=%s", entry.id, payload.date, payload.hours)
    return RedirectResponse(_with_month("/?success=1", month), status_code=303)


def _save_week(
    payload: EffortEntryCreate,
    db: Session,
    current_user: User,
    month: str | None = None,
) -> RedirectResponse:
    """Copia il form su tutti i giorni feriali della settimana della data.

    Tutti i record creati vengono associati all'utente corrente.
    """
    monday = payload.date - timedelta(days=payload.date.weekday())
    for offset in range(5):  # lun, mar, mer, gio, ven
        db.add(
            EffortEntry(
                user_id=current_user.id,
                client_id=payload.client_id,
                group_id=payload.group_id,
                activity_id=payload.activity_id,
                work_date=monday + timedelta(days=offset),
                hours_spent=payload.hours,
                notes=payload.notes,
                description=payload.description,
            )
        )
    db.commit()
    logger.info("Copia settimanale creata (settimana di %s)", payload.date.isoformat())
    return RedirectResponse(_with_month("/?success=1", month), status_code=303)


@router.get("/export", response_class=StreamingResponse, name="export_csv")
async def export_csv(
    request: Request,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
    month: str | None = None,
    year: str | None = None,
    month_num: str | None = None,
) -> StreamingResponse:
    """Esporta i record di effort in formato CSV (protetta, segregata)."""
    redirect = _require_auth(user)
    if redirect is not None:
        return redirect
    assert user is not None

    # Filtro mese risolto da anno + mese separati (S4), con fallback sul
    # vecchio parametro `month` per retrocompatibilità.
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
    stmt = _filter_by_user(stmt, user)
    if filter_month:
        stmt = stmt.where(func.strftime("%Y-%m", EffortEntry.work_date) == filter_month)
    records = db.execute(stmt).scalars().all()

    filename = f"effort_{filter_month}.csv" if filter_month else "effort_tutti.csv"
    logger.info("Export CSV generato (record=%d, mese=%s)", len(records), filter_month or "tutti")
    return StreamingResponse(
        iter([_build_csv(records)]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _build_csv(records: list[EffortEntry]) -> str:
    """Costruisce il contenuto CSV (con BOM UTF-8) dai record di effort.

    La colonna Utente mostra lo username reale dal JOIN su users; per i
    record senza proprietario (legacy) mostra una stringa vuota.
    """
    buffer = io.StringIO()
    buffer.write("\ufeff")  # BOM UTF-8 per compatibilità Excel/Windows.
    writer = csv.writer(buffer)
    writer.writerow(_CSV_HEADER)
    for record in records:
        if _is_sentinel_entry(record):
            # I giorni non lavorati non compaiono nell'export (S6).
            continue
        writer.writerow(
            [
                record.work_date.strftime("%d/%m/%Y"),
                record.client.name,
                record.group.name,
                record.activity.name,
                record.user.username if record.user is not None else "",
                record.hours_spent,
                record.notes or "",
                record.description or "",
            ]
        )
    return buffer.getvalue()


def _is_manager_view(user: User | None) -> bool:
    """True se l'utente è un manager (con un gruppo da gestire)."""
    return user is not None and is_manager(user) and user.group_id is not None


def _records_in_group_statement(db: Session, group_id: int) -> Select:
    """Restituisce lo statement SQL dei record di tutti gli utenti del gruppo.

    La vista gruppo del manager mostra i record di tutti gli utenti che
    hanno `group_id` uguale a quello del manager.
    """
    user_ids = db.execute(select(User.id).where(User.group_id == group_id)).scalars().all()
    stmt: Select = (
        select(EffortEntry)
        .options(
            selectinload(EffortEntry.client),
            selectinload(EffortEntry.group),
            selectinload(EffortEntry.activity),
            selectinload(EffortEntry.user),
        )
        .order_by(EffortEntry.work_date.desc())
    )
    if user_ids:
        stmt = stmt.where(EffortEntry.user_id.in_(user_ids))
    else:
        # Nessun membro nel gruppo: nessun record visibile.
        stmt = stmt.where(False)
    return stmt


def _records_in_group(db: Session, group_id: int, month: str | None) -> list[EffortEntry]:
    """Restituisce i record del gruppo indicato, opzionalmente filtrati per mese."""
    stmt = _records_in_group_statement(db, group_id)
    if month:
        stmt = stmt.where(func.strftime("%Y-%m", EffortEntry.work_date) == month)
    return db.execute(stmt).scalars().all()


def _year_options_in_group(db: Session, group_id: int) -> list[str]:
    """Calcola gli anni distinti (desc) dei record del gruppo del manager."""
    year_stmt = (
        select(func.strftime("%Y", EffortEntry.work_date).label("year"))
        .distinct()
        .order_by(func.strftime("%Y", EffortEntry.work_date).desc())
        .where(
            EffortEntry.user_id.in_(
                select(User.id).where(User.group_id == group_id)
            )
        )
    )
    return db.execute(year_stmt).scalars().all()


@router.get("/group", response_class=HTMLResponse, name="group_view")
async def group_view(
    request: Request,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
    month: str | None = None,
    year: str | None = None,
    month_num: str | None = None,
) -> HTMLResponse:
    """Pagina del gruppo per il manager: solo visualizzazione/esportazione.

    Il manager vede i record di tutti gli utenti del gruppo che gestisce,
    con filtro mese/anno (S4). Non c'è il form di inserimento: vista read-only.
    """
    redirect = _require_auth(user)
    if redirect is not None:
        return redirect
    assert user is not None
    if not _is_manager_view(user):
        logger.warning("Accesso negato a /group per utente %s (ruolo=%s)", user.username, user.role)
        return RedirectResponse("/", status_code=303)

    filter_month = _resolve_month(year, month_num, month)

    group = db.get(Group, user.group_id)
    records = _records_in_group(db, user.group_id, filter_month)
    year_options = _year_options_in_group(db, user.group_id)

    selected_year: str = ""
    selected_month_num: str = ""
    if filter_month and len(filter_month) == 7:
        y, m = filter_month.split("-")
        selected_year = y
        selected_month_num = m

    return templates.TemplateResponse(
        request=request,
        name="group.html",
        context={
            "app_name": APP_NAME,
            "app_version": APP_VERSION,
            "phase": "Vista gruppo (manager)",
            "group_name": group.name if group else "Gruppo",
            "records": records,
            "year_options": year_options,
            "month_options": _MESI_ITALIANI,
            "selected_year": selected_year,
            "selected_month_num": selected_month_num,
            "current_username": user.username,
            "auth_enabled": AUTH_ENABLED,
            "is_admin": is_admin(user),
            "sidebar_items": _sidebar_items(user),
        },
    )


@router.get("/group/export", response_class=StreamingResponse, name="group_export_csv")
async def group_export_csv(
    request: Request,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
    month: str | None = None,
    year: str | None = None,
    month_num: str | None = None,
) -> StreamingResponse:
    """Esporta in CSV i record del gruppo gestito dal manager."""
    redirect = _require_auth(user)
    if redirect is not None:
        return redirect
    assert user is not None
    if not _is_manager_view(user):
        logger.warning("Export negato per utente %s (ruolo=%s)", user.username, user.role)
        return RedirectResponse("/", status_code=303)

    filter_month = _resolve_month(year, month_num, month)

    group = db.get(Group, user.group_id)
    stmt = _records_in_group_statement(db, user.group_id)
    if filter_month:
        stmt = stmt.where(func.strftime("%Y-%m", EffortEntry.work_date) == filter_month)
    records = db.execute(stmt.order_by(EffortEntry.work_date.asc())).scalars().all()

    filename = f"effort_{group.name if group else 'gruppo'}_{filter_month or 'tutti'}.csv"
    logger.info("Export CSV gruppo generato (record=%d, mese=%s)", len(records), filter_month or "tutti")
    return StreamingResponse(
        iter([_build_csv(records)]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/health", name="health")
async def health() -> JSONResponse:
    """Health check: stato applicazione + check base della connettività al DB (pubblico)."""
    from app.db import engine as db_engine  # noqa: WPS433

    db_status: str = "ok"
    db_error: str | None = None
    try:
        with db_engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        db_status = "error"
        db_error = str(exc)
        logger.error("Health check: database non raggiungibile: %s", exc)

    payload: dict = {
        "app": APP_NAME,
        "version": APP_VERSION,
        "status": "ok" if db_status == "ok" else "degraded",
        "db": db_status,
    }
    if db_error is not None:
        payload["db_error"] = db_error

    status_code: int = 200 if db_status == "ok" else 503
    return JSONResponse(payload, status_code=status_code)