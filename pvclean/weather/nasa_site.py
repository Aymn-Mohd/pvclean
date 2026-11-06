"""Hourly NASA POWER weather at a named site, moved to the clock of the prices."""
from __future__ import annotations
from typing import Any
import numpy as np
import pandas as pd
import pvlib
from pvclean.core.plant import dc_power, plane_of_array
from pvclean.data import data_path

_SITE: dict[Any, Any] = {}
SITE_COLS = ("ghi", "t2m", "ws10m", "rain")


def site_table(cfg: dict[str, Any]) -> tuple[np.ndarray, pd.Timestamp]:
    """Hourly table of cfg wx_site on its original UTC clock: values with columns SITE_COLS, and the first hour. cfg wx_npz replaces the file."""
    path = cfg.get("wx_npz") or data_path("site_wx.npz")
    if path not in _SITE:
        _SITE[path] = dict(np.load(path))
    z = _SITE[path]
    return z[cfg["wx_site"]], pd.Timestamp(str(z["start_utc"]), tz="UTC")


def to_time_base(t_utc: pd.DatetimeIndex, x: np.ndarray, tz: str, year: int, how: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Hourly series x on UTC hour starts t_utc -> the price clock of calendar `year`, 365 days of 24 positions, 29 Feb dropped.
    how='hours': 24 positions per local day; a 23- or 25-hour DST day is resampled linearly to 24 positions, as the OMIE prices. how='sum': local-day totals of the true
    hours. Returns (values, naive local position stamps, true hours per local day). Hours outside the table (the first 2001 day east of UTC) are NaN and only ever reach
    nanmean climatology."""
    loc = t_utc.tz_convert(tz).tz_localize(None)
    days = pd.date_range(f"{year}-01-01", f"{year}-12-31", freq="1D")
    days = days[~((days.month == 2) & (days.day == 29))]
    n_true = np.array([int((d + pd.Timedelta(days=1)).tz_localize(tz).timestamp() - d.tz_localize(tz).timestamp()) // 3600 for d in days])
    left = np.searchsorted(loc.values, days.values); right = np.searchsorted(loc.values, (days + pd.Timedelta(days=1)).values)
    out = np.full(len(days) if how == "sum" else len(days) * 24, np.nan)
    for i in range(len(days)):
        v = x[left[i]:right[i]]
        if how == "sum":
            out[i] = v.sum() if len(v) else np.nan
        elif len(v) == n_true[i]:
            out[i * 24:i * 24 + 24] = v if len(v) == 24 else np.interp(np.linspace(0, 1, 24), np.linspace(0, 1, len(v)), v)
        else:                                   # the table starts inside this day: keep the hours it has, by wall clock
            out[i * 24 + loc[left[i]:right[i]].hour.values] = v
    stamps = (days.values[:, None] + np.arange(24)[None, :].astype("timedelta64[h]")).ravel()
    return out, stamps, n_true


def site_year(year: int, cfg: dict[str, Any]) -> dict[str, Any]:
    """One real calendar year at cfg's site. Production is computed on the true UTC clock (sun position at mid-hour: the NASA POWER stamp is the hour start) with the
    Dubai chain, and only then moved to cfg time_base, so the sun stays right on DST days. Wind is the hourly WS10M unless cfg wx_wind is a number. Cached per process;
    callers must not modify the arrays."""
    key = (cfg["wx_site"], year, cfg["lat"], cfg["lon"], cfg["alt"], cfg["tilt"], cfg["azimuth"], cfg["gamma"], cfg["time_base"], cfg.get("wx_wind"), cfg.get("wx_npz"))
    if key in _SITE:
        return _SITE[key]
    a, t0 = site_table(cfg)
    i0 = max(0, int((pd.Timestamp(f"{year - 1}-12-30", tz="UTC") - t0) / pd.Timedelta("1h")))
    i1 = min(len(a), int((pd.Timestamp(f"{year + 1}-01-03", tz="UTC") - t0) / pd.Timedelta("1h")))
    a = a[i0:i1]
    t = pd.date_range(t0 + pd.Timedelta(hours=i0), periods=len(a), freq="1h")
    t_mid = t + pd.Timedelta("30min")
    sp = pvlib.location.Location(cfg["lat"], cfg["lon"], "UTC", cfg["alt"]).get_solarposition(t_mid)
    zen = sp["zenith"].values
    ghi = np.where(zen < 90, np.clip(a[:, 0], 0, None), 0.0)
    poa = plane_of_array(ghi, zen, sp["azimuth"].values, t_mid, cfg)
    wind = a[:, 2] if cfg.get("wx_wind") is None else cfg["wx_wind"]
    pdc = dc_power(poa, a[:, 1], wind, cfg)
    pdc_l, stamps, n_true = to_time_base(t, pdc, cfg["time_base"], year, "hours")
    rain = to_time_base(t, a[:, 3], cfg["time_base"], year, "sum")[0]
    _SITE[key] = dict(pdc=pdc_l, rain=rain, ts=stamps, hours=n_true)
    return _SITE[key]


def weather_site(seed: int, cfg: dict[str, Any]) -> dict[str, Any]:
    """Real weather at cfg's site for the price year this seed plays: the weather year follows the same index as the price year (cfg real_years[seed % len], mapped to a
    calendar year by cfg wx_site_years); dust and exposure stay seeded."""
    k = cfg["real_years"][seed % len(cfg["real_years"])]
    a = site_year(cfg["wx_site_years"][k], cfg)
    return dict(pdc=a["pdc"], rain=a["rain"] * cfg.get("rain_scale", 1.0), clear_pdc=None)
