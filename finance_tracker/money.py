"""Money handling.

All amounts are stored as integer pence. Floats are never used for money,
because binary floating point cannot represent values like 0.10 exactly.
"""
from decimal import Decimal, InvalidOperation

MAX_PENCE = 100_000_000_00  # £100m upper bound - rejects obviously bad input


def parse_amount(text: str) -> int:
    """Convert a user-entered amount like '12.5' or '£1,200.00' to pence.

    Raises ValueError for anything that is not a positive amount with at
    most two decimal places.
    """
    cleaned = str(text).strip().replace("£", "").replace(",", "")
    try:
        value = Decimal(cleaned)
    except InvalidOperation:
        raise ValueError(f"'{text}' is not a valid amount") from None
    if not value.is_finite():
        raise ValueError(f"'{text}' is not a valid amount")
    if value <= 0:
        raise ValueError("Amount must be greater than zero")
    if value.as_tuple().exponent < -2:
        raise ValueError("Amount can have at most two decimal places")
    pence = int(value * 100)
    if pence > MAX_PENCE:
        raise ValueError("Amount is unrealistically large")
    return pence


def format_pence(pence: int) -> str:
    """Format pence as a pound string, e.g. -1234 -> '-£12.34'."""
    sign = "-" if pence < 0 else ""
    pence = abs(pence)
    return f"{sign}£{pence // 100:,}.{pence % 100:02d}"
