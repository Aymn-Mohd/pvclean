"""NASA POWER years at Dubai, local time."""
from __future__ import annotations
from typing import Any
import numpy as np
import pandas as pd
from pvclean.core.plant import clear_sky, dc_power, plane_of_array
from pvclean.data import data_path

_WX: dict[str, Any] = {}


def weather_dubai(seed: int, cfg: dict[str, Any]) -> dict[str, Any]:
    """Replays one real year: GHI, T2M and hourly rain from file. The year is chosen by seed from cfg wx_years; dust and exposure stay seeded."""
    if "npz" not in _WX:
        _WX["npz"] = np.load(data_path("dubai_wx.npz"))
    yrs = cfg["wx_years"]
    a = _WX["npz"][str(yrs[seed % len(yrs)])]
    cs = clear_sky(cfg)
    zen = cs["sp"]["zenith"].values
    ghi = np.where(zen < 90, np.clip(a[:, 0], 0, None), 0.0)
    poa = plane_of_array(ghi, zen, cs["sp"]["azimuth"].values, cs["t"] + pd.Timedelta("30min"), cfg)
    rain = a[:, 3].reshape(365, 24).sum(1) * cfg.get("rain_scale", 1.0)
    return dict(pdc=dc_power(poa, a[:, 2], cfg["wind_default"], cfg), rain=rain, clear_pdc=None)
