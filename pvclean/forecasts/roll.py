"""F2: causal rolling hour-of-day mean."""
from __future__ import annotations
import numpy as np
from .base import Forecast, rolling_profile


class Rolling(Forecast):
    """Mean of the last 28 days by default; climatology until min_hist days have passed."""
    name = "roll"

    def cutoff(self, d: int, n_hours: int) -> int:
        return 24 * d

    def predict(self, d: int, hh: np.ndarray, known: np.ndarray, vexp: np.ndarray, min_hist: int, roll_days: int) -> np.ndarray:
        if d < min_hist:
            return vexp[hh].copy()
        return rolling_profile(d, len(hh), known, roll_days)
