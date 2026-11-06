"""F4: all realised values in the planning window. An oracle, never a deployable result."""
from __future__ import annotations
import numpy as np
from .base import Forecast


class Perfect(Forecast):
    """Reads the realised values of the planning window."""
    name = "perfect"
    deployable = False

    def cutoff(self, d: int, n_hours: int) -> int:
        return 24 * d + n_hours

    def predict(self, d: int, hh: np.ndarray, known: np.ndarray, vexp: np.ndarray, min_hist: int, roll_days: int) -> np.ndarray:
        return known[hh]
