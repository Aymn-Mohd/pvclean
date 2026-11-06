"""The public model calls in one place, with the default parameter set as the default argument."""
from __future__ import annotations
from typing import Any
import numpy as np
from pvclean.config import CONFIG, merged
from pvclean.contracts import get_contract, hourly_value as _hourly_value
from pvclean.core.inputs import climatology_pdc as _climatology_pdc, planner_inputs as _planner_inputs
from pvclean.core.plant import clear_sky as _clear_sky, delivered, row_ac
from pvclean.core.robot import blackout_mask, mission_record, mission_time, pack, robot_up, schedule_violations
from pvclean.core.simulator import STATE_KEYS, simulate
from pvclean.core.soiling import dust as _dust, expected_increment, exposure as _exposure, rain_forecast
from pvclean.forecasts import fc_value
from pvclean.markets import contract_value, get_market, spot_prices as _spot_prices
from pvclean.weather import SITE_COLS, site_table, site_year, to_time_base, weather as _weather, weather_site
from pvclean.weather.nasa_dubai import weather_dubai as weather_real

__all__ = ["CONFIG", "SITE_COLS", "STATE_KEYS", "blackout_mask", "clear_sky", "climatology_pdc", "contract_value", "delivered", "dust", "expected_increment", "exposure", "fc_value",
           "hourly_value", "merged", "mission_record", "mission_time", "pack", "planner_inputs", "rain_forecast", "real_value_year", "robot_up", "row_ac", "schedule_violations",
           "simulate", "site_table", "site_year", "spot_prices", "to_time_base", "weather", "weather_real", "weather_site"]


def clear_sky(cfg: dict[str, Any] = CONFIG) -> dict[str, Any]:
    """Clear-sky geometry of the site."""
    return _clear_sky(cfg)


def weather(seed: int, cfg: dict[str, Any] = CONFIG) -> dict[str, Any]:
    """Hourly DC power per kWp and daily rain of one simulated year."""
    return _weather(seed, cfg)


def spot_prices(seed: int, cfg: dict[str, Any] = CONFIG) -> np.ndarray:
    """Hourly spot prices [USD/kWh]."""
    return _spot_prices(seed, cfg)


def hourly_value(contract: str, spot: np.ndarray, cfg: dict[str, Any] = CONFIG) -> np.ndarray:
    """Marginal revenue per delivered kWh in each hour."""
    return _hourly_value(contract, spot, cfg)


def exposure(cfg: dict[str, Any] = CONFIG, site_seed: int | None = None, hetero: float = 1.0) -> np.ndarray:
    """Relative soiling exposure of each row."""
    return _exposure(cfg, site_seed, hetero)


def dust(seed: int, cfg: dict[str, Any] = CONFIG) -> tuple[np.ndarray, np.ndarray]:
    """Site increment per day and the row noise."""
    return _dust(seed, cfg)


def climatology_pdc(cfg: dict[str, Any] = CONFIG, seeds: Any = None) -> np.ndarray:
    """The planner's production forecast."""
    return _climatology_pdc(cfg, seeds)


def planner_inputs(contract: str, cfg: dict[str, Any] = CONFIG, train_seeds: Any = None) -> tuple[np.ndarray, np.ndarray, float]:
    """Production climatology, expected hourly value and the constant price of the econ baseline."""
    return _planner_inputs(contract, cfg, train_seeds)


def real_value_year(contract: str, seed: int, cfg: dict[str, Any]) -> tuple[np.ndarray, np.ndarray | None]:
    """Interval-level contract value of one real year and its warm-up."""
    return get_market(cfg["real_value"]).interval_value(get_contract(contract), seed, cfg)
