"""Merchant sale at spot."""
from __future__ import annotations
from typing import Any
import numpy as np
from .base import Contract


class Merchant(Contract):
    """Earns the spot price; the plant may curtail at negative prices."""
    name = "merchant"
    interval_key = "merchant"

    def hourly_value(self, spot: np.ndarray, cfg: dict[str, Any]) -> np.ndarray:
        return np.maximum(spot, 0.0)

    def from_interval(self, a: np.ndarray, cfg: dict[str, Any]) -> np.ndarray:
        return a
