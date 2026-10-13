"""Input validation helpers shared by the CLI and the CSV importer."""
import re
from datetime import date

TYPES = ("income", "expense")
_CATEGORY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 &/_-]{0,39}$")
_MONTH_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
MAX_NOTE = 200


def validate_type(value: str) -> str:
    value = str(value).strip().lower()
    if value not in TYPES:
        raise ValueError(f"Type must be one of: {', '.join(TYPES)}")
    return value


def validate_category(value: str) -> str:
    value = str(value).strip()
    if not _CATEGORY_RE.match(value):
        raise ValueError(
            "Category must be 1-40 characters: letters, numbers, spaces, & / _ -"
        )
    return value.lower()


def validate_date(value: str) -> str:
    """Accept YYYY-MM-DD and return it in ISO form."""
    try:
        return date.fromisoformat(str(value).strip()).isoformat()
    except ValueError:
        raise ValueError(f"'{value}' is not a valid date (use YYYY-MM-DD)") from None


def validate_month(value: str) -> str:
    value = str(value).strip()
    if not _MONTH_RE.match(value):
        raise ValueError(f"'{value}' is not a valid month (use YYYY-MM)")
    return value


def validate_note(value: str) -> str:
    value = "" if value is None else str(value).strip()
    if len(value) > MAX_NOTE:
        raise ValueError(f"Note must be {MAX_NOTE} characters or fewer")
    # Strip control characters so notes can't mess with terminal output.
    return "".join(ch for ch in value if ch.isprintable())
