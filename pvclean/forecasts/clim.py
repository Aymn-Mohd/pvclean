"""CLIM: expected value from the training years, no realised values."""
from __future__ import annotations
import numpy as np
from .base import Forecast


class Climatology(Forecast):
    """F0 and F1: climatology of other price years. It only differs in which training years built vexp."""
    name = "clim"

    def cutoff(self, d: int, n_hours: int) -> int:
        return 0

    def predict(self, d: int, hh: np.ndarray, known: np.ndarray, vexp: np.ndarray, min_hist: int, roll_days: int) -> np.ndarray:
        return vexp[hh]
