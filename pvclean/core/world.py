"""The functions that define what is true in a simulated year. A study can pass a different World instead of changing module state."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Callable
import numpy as np
from pvclean.contracts import hourly_value as _hourly_value
from pvclean.weather import weather as _weather
from .soiling import dust as _dust, exposure as _exposure, rain_forecast as _rain_forecast


@dataclass(frozen=True)
class World:
    """weather(seed, cfg), dust(seed, cfg), exposure(cfg, hetero=), hourly_value(contract, spot, cfg), rain_forecast(rain, seed, cfg)."""
    weather: Callable[..., dict[str, Any]] = _weather
    dust: Callable[..., tuple[np.ndarray, np.ndarray]] = _dust
    exposure: Callable[..., np.ndarray] = _exposure
    hourly_value: Callable[..., np.ndarray] = _hourly_value
    rain_forecast: Callable[..., np.ndarray] = _rain_forecast


DEFAULT_WORLD = World()
