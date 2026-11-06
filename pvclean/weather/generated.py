"""Dubai weather generator: seeded clear-sky index, haze and rain on clear-sky irradiance."""
from __future__ import annotations
from typing import Any
import numpy as np
import pandas as pd
from pvclean.core.plant import clear_sky, dc_power, plane_of_array


def weather_generated(seed: int, cfg: dict[str, Any]) -> dict[str, Any]:
    """Hourly DC power per kWp and daily rain [mm] for one generated year."""
    rng = np.random.default_rng(seed)
    cs = clear_sky(cfg)
    nd = 365
    mday = cs["month"][::24]
    k = np.full(nd, cfg["wx_clear_index"]) + rng.normal(0, cfg["wx_clear_index_sd"], nd)
    haze = rng.random(nd) < np.array(cfg["month_haze_p"])[mday]
    k[haze] = rng.uniform(*cfg["wx_haze_index"], haze.sum())
    rainy = rng.random(nd) < np.minimum(np.array(cfg["month_rain_p"])[mday] * cfg.get("rain_scale", 1.0), cfg["wx_rain_p_cap"])
    rain = np.where(rainy, rng.gamma(*cfg["wx_rain_gamma"], nd), 0.0)
    k[rainy] = rng.uniform(*cfg["wx_rain_index"], rainy.sum())
    kh = np.repeat(np.clip(k, *cfg["wx_index_clip"]), 24)
    ghi = cs["ghi"] * kh
    zen = cs["sp"]["zenith"].values
    poa = plane_of_array(ghi, zen, cs["sp"]["azimuth"].values, cs["t"] + pd.Timedelta("30min"), cfg)
    doy = np.arange(8760) / 24.0
    hod = cs["hour"]
    t_amb = cfg["wx_temp_mean"] + cfg["wx_temp_year_amp"] * np.sin(2 * np.pi * (doy - cfg["wx_temp_year_day"]) / 365) + cfg["wx_temp_day_amp"] * np.sin(2 * np.pi * (hod - cfg["wx_temp_day_hour"]) / 24)
    return dict(pdc=dc_power(poa, t_amb, cfg["wind_default"], cfg), rain=rain, clear_pdc=None)
