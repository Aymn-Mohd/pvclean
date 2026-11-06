"""Real price years from the data cache: hourly means (real_prices.npz) and interval-level values (real_prices_v2.npz)."""
from __future__ import annotations
from typing import Any
import numpy as np
from pvclean.contracts.base import Contract
from pvclean.data import data_path
from .base import Market

_NPZ: dict[str, Any] = {}
_VAL: dict[str, dict[str, np.ndarray]] = {}


class RealMarket(Market):
    """One series of a price file, chosen by name; the year follows cfg real_years[seed % len]."""

    def __init__(self, name: str) -> None:
        self.name = name

    def spot(self, seed: int, cfg: dict[str, Any]) -> np.ndarray:
        if "npz" not in _NPZ:
            _NPZ["npz"] = np.load(data_path("real_prices.npz"))
        arr = _NPZ["npz"][self.name]
        yrs = cfg["real_years"]
        return arr[yrs[seed % len(yrs)]]

    def interval_value(self, contract: Contract, seed: int, cfg: dict[str, Any]) -> tuple[np.ndarray, np.ndarray | None]:
        """Hourly contract value from interval prices and its 28-day warm-up. merchant = mean of max(p, 0) over the hour's intervals; ppa = cfg ppa x share of the hour's
        intervals with p >= 0. Warm-up is None if the file has none or cfg value_warm is False. cfg value_npz replaces the file."""
        path = cfg.get("value_npz") or data_path("real_prices_v2.npz")
        if path not in _VAL:
            _VAL[path] = dict(np.load(path))
        z = _VAL[path]; yrs = cfg["real_years"]; k = yrs[seed % len(yrs)]
        key = contract.interval_key
        val = contract.from_interval(z[f"{self.name}|{key}"][k], cfg)
        wk = f"{self.name}|warm_{key}"
        warm = contract.from_interval(z[wk][k], cfg) if (wk in z and cfg.get("value_warm", True)) else None
        return val, warm
