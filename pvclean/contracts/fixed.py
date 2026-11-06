"""Fixed tariff."""
from __future__ import annotations
from typing import Any
import numpy as np
from .base import Contract


class FixedTariff(Contract):
    """Every delivered kWh earns the tariff."""
    name = "fixed"

    def hourly_value(self, spot: np.ndarray, cfg: dict[str, Any]) -> np.ndarray:
        return np.full(8760, cfg["tariff"])
