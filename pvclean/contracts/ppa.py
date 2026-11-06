"""Power purchase agreement with a negative-price clause."""
from __future__ import annotations
from typing import Any
import numpy as np
from .base import Contract


class PPA(Contract):
    """Earns the PPA price, with no payment when spot is negative."""
    name = "ppa"
    interval_key = "ppa_frac"

    def hourly_value(self, spot: np.ndarray, cfg: dict[str, Any]) -> np.ndarray:
        return np.where(spot >= 0, cfg["ppa"], 0.0)

    def from_interval(self, a: np.ndarray, cfg: dict[str, Any]) -> np.ndarray:
        return cfg["ppa"] * a
