"""Servizio di esportazione CSV per i record di effort.

Centralizza header, costanti condivise e la costruzione del contenuto CSV
(con BOM UTF-8) usati da tutti i router che espongono un export
(`web`, `admin_dashboard`, `admin_records_export`, `admin_lookup`).
I giorni non lavorati (record sentinella "NON LAVORATO", S6) vengono
**sempre** esclusi dall'export, per tutti i ruoli.
"""
from __future__ import annotations

import csv
import io

from app.core.seed import SENTINEL_NAME
from app.models import EffortEntry

# Header del CSV di export, coerente con le colonne della tabella.
CSV_HEADER = [
    "Data",
    "Cliente",
    "Gruppo",
    "Attività",
    "Utente",
    "Ore",
    "Note",
    "Descrizione attività",
]

# Nomi dei mesi in italiano (indice 0 vuoto, 1..12).
MESI_ITALIANI = [
    "", "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
    "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre",
]


def is_sentinel_entry(record: EffortEntry) -> bool:
    """True se il record è un giorno non lavorato (cliente sentinella)."""
    return record.client is not None and record.client.name == SENTINEL_NAME


def build_csv(records: list[EffortEntry]) -> str:
    """Costruisce il contenuto CSV (con BOM UTF-8) dai record di effort.

    I giorni non lavorati (record con cliente sentinella "NON LAVORATO", S6)
    vengono esclusi dall'export per tutti i ruoli. La colonna Utente mostra lo
    username reale dal JOIN su users; per i record senza proprietario (legacy)
    mostra una stringa vuota.
    """
    buffer = io.StringIO()
    buffer.write("\ufeff")  # BOM UTF-8 per compatibilità Excel/Windows.
    writer = csv.writer(buffer)
    writer.writerow(CSV_HEADER)
    for record in records:
        if is_sentinel_entry(record):
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