"""Macro formatting: rounding half up with Decimal, so a printed number does not depend on binary float rounding."""
from __future__ import annotations
from decimal import ROUND_HALF_UP, Decimal


def rnd(x: float, d: int = 0) -> str:
    """x rounded half up to d decimals, from its shortest repr."""
    q = Decimal(1).scaleb(-d)
    return str(Decimal(repr(x)).quantize(q, rounding=ROUND_HALF_UP))
