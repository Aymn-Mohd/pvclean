"""FHW: causal rolling hour-of-day mean, kept apart for weekdays and weekend days."""
from __future__ import annotations
from typing import Any
import numpy as np
from .roll import Rolling


class RollingDayType(Rolling):
    """Mean of the last roll_days days by hour of day, using only past days of the target day's type (weekday or weekend). The type of each day comes from the price
    file's own timestamps (day_type, True = Saturday or Sunday), so no information about prices reaches it. A type with no past day in the window falls back to all
    past days. No public holidays."""
    name = "roll_hw"
    uses_day_type = True

    def predict(self, d: int, hh: np.ndarray, known: np.ndarray, vexp: np.ndarray, min_hist: int, roll_days: int, day_type: np.ndarray | None = None) -> np.ndarray:
        if day_type is None:
            raise ValueError("roll_hw needs day_type: run it through the simulator, which supplies the calendar")
        if d < min_hist:
            return vexp[hh].copy()
        N = min(roll_days, d)
        past = known[(d - N) * 24:d * 24].reshape(N, 24); pt = np.asarray(day_type[d - N:d], bool)
        prof = {t: past[pt == t].mean(0) if (pt == t).any() else past.mean(0) for t in (False, True)}
        days = np.minimum(hh // 24, len(day_type) - 1); hod = hh % 24
        tgt = np.asarray(day_type, bool)[days]
        return np.where(tgt, prof[True][hod], prof[False][hod])


def day_types(cfg: dict[str, Any], seed: int) -> np.ndarray:
    """Weekend flags of the warm-up days and the 365 days of the price year that seed uses, from the price file's local timestamps (29 February is already absent)."""
    from pvclean.data import data_path
    z = np.load(cfg.get("value_npz") or data_path("real_prices_v2.npz"))
    yrs = cfg["real_years"]; ts = z[f"{cfg['real_value']}|ts"][yrs[seed % len(yrs)]]
    day = ts[::24].astype("datetime64[D]")
    W = cfg["price_warm_days"]
    warm = day[0] - np.arange(W, 0, -1).astype("timedelta64[D]")
    allday = np.concatenate([warm, day])
    dow = (allday.astype("int64") + 3) % 7          # 1970-01-01 was a Thursday: Monday = 0
    return dow >= 5
