"""Contract interface: what one delivered kWh earns in each hour."""
from __future__ import annotations
from typing import Any
import numpy as np


class Contract:
    """A contract values delivered energy. `capped` limits plant export. `interval_key` names the interval-level array of a price file, if the contract has one."""
    name = ""
    capped = False
    interval_key: str | None = None

    def hourly_value(self, spot: np.ndarray, cfg: dict[str, Any]) -> np.ndarray:
        """Marginal revenue per delivered kWh in each hour."""
        raise NotImplementedError

    def from_interval(self, a: np.ndarray, cfg: dict[str, Any]) -> np.ndarray:
        """Hourly value from the contract's interval-level array."""
        raise NotImplementedError
