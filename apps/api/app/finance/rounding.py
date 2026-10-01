from decimal import Decimal, ROUND_HALF_EVEN
from typing import Optional


def round_currency(value: Optional[Decimal], places: int = 2) -> Optional[Decimal]:
    """Rounds a currency Decimal value using ROUND_HALF_EVEN (§19)."""
    if value is None:
        return None
    fmt = Decimal("10") ** -places
    return value.quantize(fmt, rounding=ROUND_HALF_EVEN)


def round_percent(value: Optional[Decimal], places: int = 4) -> Optional[Decimal]:
    """Rounds a percentage Decimal value (e.g. 0.1234 -> 12.34%) using ROUND_HALF_EVEN (§19)."""
    if value is None:
        return None
    fmt = Decimal("10") ** -places
    return value.quantize(fmt, rounding=ROUND_HALF_EVEN)


def round_ratio(value: Optional[Decimal], places: int = 6) -> Optional[Decimal]:
    """Rounds a ratio/weight Decimal value using ROUND_HALF_EVEN (§19)."""
    if value is None:
        return None
    fmt = Decimal("10") ** -places
    return value.quantize(fmt, rounding=ROUND_HALF_EVEN)


def round_quantity(value: Optional[Decimal], places: int = 8) -> Optional[Decimal]:
    """Rounds a share quantity Decimal value using ROUND_HALF_EVEN (§19)."""
    if value is None:
        return None
    fmt = Decimal("10") ** -places
    return value.quantize(fmt, rounding=ROUND_HALF_EVEN)
