"""A new forecast in one file: yesterday repeats."""
import numpy as np
from pvclean.forecasts.base import Forecast


class Yesterday(Forecast):
    name = "yesterday"

    def cutoff(self, d, n_hours):
        return 24 * d

    def predict(self, d, hh, known, vexp, min_hist, roll_days):
        if d == 0:
            return vexp[hh].copy()
        return np.tile(known[(d - 1) * 24:d * 24], len(hh) // 24 + 1)[:len(hh)]
