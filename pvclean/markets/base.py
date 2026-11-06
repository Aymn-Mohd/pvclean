"""Market interface: hourly spot prices of one simulated year."""
from __future__ import annotations
from typing import Any
import numpy as np


class Market:
    """A market gives hourly spot prices [USD/kWh]. Real markets also give interval-level contract values."""
    name = ""

    def spot(self, seed: int, cfg: dict[str, Any]) -> np.ndarray:
        """Hourly prices of the year that this seed plays."""
        raise NotImplementedError
