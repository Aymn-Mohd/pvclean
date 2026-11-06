"""Stylised high-solar merchant market. A scenario, not a forecast of any market."""
from __future__ import annotations
from typing import Any
import numpy as np
from pvclean.core.plant import clear_sky
from .base import Market


class GeneratedMarket(Market):
    """Base price, evening peak, seasonal midday solar depression, daily and hourly noise [USD/kWh]."""
    name = "generated"

    def spot(self, seed: int, cfg: dict[str, Any]) -> np.ndarray:
        rng = np.random.default_rng(seed + cfg["seed_offset_price"])
        cs = clear_sky(cfg)
        hod, m = cs["hour"], cs["month"]
        base = cfg["price_base"] + cfg["price_base_amp"] * np.cos(2 * np.pi * (m - cfg["price_base_month"]) / 12)
        evening = cfg["price_evening"] * np.exp(-0.5 * ((hod - cfg["price_evening_hour"]) / cfg["price_evening_width"]) ** 2)
        solar_share = np.clip(cs["ghi"] / cfg["price_solar_ref"], 0, 1)
        depress = np.array(cfg["price_depress_month"])[m]
        depress = depress * cfg.get("price_depress_scale", 1.0)
        daily = np.repeat(rng.normal(0, cfg["price_daily_sd"], 365), 24)
        noise = rng.normal(0, cfg["price_noise_sd"], 8760)
        return base + evening - depress * solar_share ** cfg["price_solar_exp"] + daily + noise
