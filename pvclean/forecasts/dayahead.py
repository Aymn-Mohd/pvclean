"""F3: F2 plus the 24 hours of the operating day, published the day before."""
from __future__ import annotations
import numpy as np
from .roll import Rolling


class DayAhead(Rolling):
    """A day-ahead auction for day d clears on day d-1, so the values of day d are known at the decision."""
    name = "dayahead"

    def cutoff(self, d: int, n_hours: int) -> int:
        return 24 * d + 24

    def predict(self, d: int, hh: np.ndarray, known: np.ndarray, vexp: np.ndarray, min_hist: int, roll_days: int) -> np.ndarray:
        vv = super().predict(d, hh, known, vexp, min_hist, roll_days).copy()
        vv[:24] = known[hh[:24]]
        return vv
