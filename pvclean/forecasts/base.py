"""Causal forecast interface.

Hour index h = 24*day + hour-of-day, local standard time of the market or plant. The robot works at night, so the decision for day d is taken at hour
index 24*d, after the previous day has settled, and runs before day-d production. A provider receives only the prefix val[:cutoff]; later values cannot
be reached.
"""
from __future__ import annotations
import numpy as np


class Forecast:
    """One forecast provider. Subclasses set the information cutoff and the forecast."""
    name = ""
    deployable = True

    def cutoff(self, d: int, n_hours: int) -> int:
        """First hour index of the realised series that is not available at the decision for day d."""
        raise NotImplementedError

    def predict(self, d: int, hh: np.ndarray, known: np.ndarray, vexp: np.ndarray, min_hist: int, roll_days: int) -> np.ndarray:
        """Expected contract value for hours hh, from `known` and the training-year expectation vexp."""
        raise NotImplementedError


def rolling_profile(d: int, n: int, known: np.ndarray, roll_days: int) -> np.ndarray:
    """Mean hour-of-day profile of the last roll_days days, tiled over n hours."""
    N = min(roll_days, d)
    prof = known[(d - N) * 24:d * 24].reshape(N, 24).mean(0)
    return np.tile(prof, n // 24 + 1)[:n]
