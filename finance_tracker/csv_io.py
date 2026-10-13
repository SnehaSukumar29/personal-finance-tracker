"""CSV import and export.

Export neutralises spreadsheet formula injection (CWE-1236): any text cell
starting with =, +, -, @, tab or carriage return is prefixed with a single
quote so Excel/LibreOffice treat it as text instead of executing it.

Import validates every row first and only writes to the database if the
whole file is valid, so a bad file can never leave half its rows behind.
"""
import csv

from finance_tracker.db import Database
from finance_tracker.money import parse_amount
from finance_tracker.validation import (
    validate_category,
    validate_date,
    validate_note,
    validate_type,
)

HEADER = ["date", "type", "amount", "category", "note"]
_DANGEROUS_PREFIXES = ("=", "+", "-", "@", "\t", "\r")
MAX_IMPORT_ROWS = 10_000


def sanitise_cell(value: str) -> str:
    text = str(value)
    if text.startswith(_DANGEROUS_PREFIXES):
        return "'" + text
    return text


def unsanitise_cell(value: str) -> str:
    """Reverse sanitise_cell so exported files round-trip cleanly on import."""
    text = str(value)
    if text.startswith("'") and text[1:].startswith(_DANGEROUS_PREFIXES):
        return text[1:]
    return text


def export_csv(db: Database, path: str, month: str = None) -> int:
    rows = db.list_transactions(month=month)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(HEADER)
        for tx in rows:
            amount = f"{tx.amount_pence // 100}.{tx.amount_pence % 100:02d}"  # e.g. 12.50
            writer.writerow([
                tx.tx_date,
                tx.type,
                amount,
                sanitise_cell(tx.category),
                sanitise_cell(tx.note),
            ])
    return len(rows)


class CsvImportError(Exception):
    """Raised when a CSV file fails validation. Holds every row error."""

    def __init__(self, errors: list):
        self.errors = errors
        super().__init__(f"{len(errors)} invalid row(s)")


def import_csv(db: Database, path: str) -> int:
    parsed, errors = [], []
    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        missing = [h for h in HEADER if h not in (reader.fieldnames or [])]
        if missing:
            raise CsvImportError([f"Missing column(s): {', '.join(missing)}"])
        for line_no, row in enumerate(reader, start=2):
            if line_no - 1 > MAX_IMPORT_ROWS:
                raise CsvImportError([f"File has more than {MAX_IMPORT_ROWS} rows"])
            try:
                parsed.append((
                    validate_type(row["type"]),
                    parse_amount(row["amount"]),
                    validate_category(row["category"]),
                    validate_date(row["date"]),
                    validate_note(unsanitise_cell(row.get("note") or "")),
                ))
            except ValueError as exc:
                errors.append(f"Line {line_no}: {exc}")
    if errors:
        raise CsvImportError(errors)
    return db.add_many(parsed)
