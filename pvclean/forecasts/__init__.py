"""Forecast registry and the calls the simulator and the audits use. To add a forecast: one new file here and one line in REGISTRY."""
from __future__ import annotations
import numpy as np
from .base import Forecast
from .clim import Climatology
from .dayahead import DayAhead
from .perfect import Perfect
from .roll import Rolling
from .roll_hw import RollingDayType, day_types

REGISTRY: dict[str, Forecast] = {
    "clim": Climatology(),
    "clim_prev": Climatology(),
    "roll": Rolling(),
    "dayahead": DayAhead(),
    "perfect": Perfect(),
    "roll_hw": RollingDayType(),
}
# Public scenario names used in the paper.
SCENARIOS = {"F0": "clim", "F1": "clim", "F2": "roll", "F3": "dayahead", "F4": "perfect"}
DEPLOYABLE = {name: REGISTRY[mode].deployable for name, mode in SCENARIOS.items()}


def register(name: str, forecast: Forecast) -> None:
    """Adds a forecast at run time."""
    REGISTRY[name] = forecast


def info_cutoff(mode: str, d: int, n_hours: int) -> int:
    """First hour index of the realised series that is not available at the decision for day d."""
    if mode not in REGISTRY:
        raise ValueError(mode)
    return REGISTRY[mode].cutoff(d, n_hours)


def value_forecast(mode: str, d: int, hh: np.ndarray, val: np.ndarray, vexp: np.ndarray, min_hist: int = 7, roll_days: int = 28, day_type: np.ndarray | None = None) -> np.ndarray:
    """Expected contract value per hour for hour indices hh, from what is known at day d. Only val[:cutoff] reaches the provider. day_type (weekend flag per day, calendar only) is
    passed only to forecasts that use it."""
    known = val[:info_cutoff(mode, d, len(hh))]
    if day_type is not None and getattr(REGISTRY[mode], "uses_day_type", False):
        return REGISTRY[mode].predict(d, hh, known, vexp, min_hist, roll_days, day_type=day_type)
    return REGISTRY[mode].predict(d, hh, known, vexp, min_hist, roll_days)


def forecast_record(mode: str, d: int, n_hours: int) -> dict[str, int]:
    """Timestamps of one decision: decision time, information cutoff, issue time, horizon, execution."""
    return dict(decision_time=24 * d, information_cutoff=info_cutoff(mode, d, n_hours), forecast_issue_time=24 * d, forecast_horizon_hours=n_hours, execution_time=24 * d + 1)


def fc_value(mode: str, d: int, hh: np.ndarray, val: np.ndarray, vexp: np.ndarray, min_hist: int = 7, warm: np.ndarray | None = None, roll_days: int = 28,
             day_type: np.ndarray | None = None) -> np.ndarray:
    """Forecast with a warm-up series: the hours just before day 0 count as history, so day d of the year is day d + W of warm ++ val. day_type, if given, covers the
    warm-up days and the year (day_types())."""
    if warm is None or mode in ("clim", "clim_prev"):
        dt = None if day_type is None else day_type[-(len(val) // 24):]
        return value_forecast(mode, d, hh, val, vexp, min_hist=min_hist, roll_days=roll_days, day_type=dt)
    W = len(warm) // 24
    ext = np.concatenate([warm, val])
    vx = np.concatenate([np.full(24 * W, np.nan), vexp])      # never read: d + W >= W >= min_hist
    dt = None if day_type is None else day_type[-(W + len(val) // 24):]
    return value_forecast(mode, d + W, hh + 24 * W, ext, vx, min_hist=min_hist, roll_days=roll_days, day_type=dt)
