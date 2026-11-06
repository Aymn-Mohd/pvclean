"""Plant and production: clear-sky geometry, the pvlib chain from GHI to DC power, inverter clipping and export limit."""
from __future__ import annotations
from typing import Any
import numpy as np
import pandas as pd
import pvlib

_CS_CACHE: dict[tuple, dict[str, Any]] = {}


def clear_sky(cfg: dict[str, Any]) -> dict[str, Any]:
    """Clear-sky geometry of the site at mid-hour, cached per site and year."""
    key = (cfg["lat"], cfg["lon"], cfg["year"], cfg["tilt"], cfg["tz"])
    if key in _CS_CACHE:
        return _CS_CACHE[key]
    loc = pvlib.location.Location(cfg["lat"], cfg["lon"], cfg["tz"], cfg["alt"])
    t = pd.date_range(f"{cfg['year']}-01-01", f"{cfg['year']+1}-01-01", freq="1h", tz=cfg["tz"], inclusive="left")
    t_mid = t + pd.Timedelta("30min")
    sp = loc.get_solarposition(t_mid)
    cs = loc.get_clearsky(t_mid, solar_position=sp)
    out = dict(t=t, sp=sp, ghi=cs.ghi.values, dni_extra=pvlib.irradiance.get_extra_radiation(t_mid).values, month=t.month.values - 1, hour=t.hour.values)
    _CS_CACHE[key] = out
    return out


def plane_of_array(ghi: np.ndarray, zenith: np.ndarray, sun_azimuth: np.ndarray, t_mid: pd.DatetimeIndex, cfg: dict[str, Any]) -> np.ndarray:
    """Erbs split and isotropic transposition to the module plane [W/m2]."""
    erbs = pvlib.irradiance.erbs(ghi, zenith, t_mid)
    poa = pvlib.irradiance.get_total_irradiance(cfg["tilt"], cfg["azimuth"], zenith, sun_azimuth, erbs["dni"], ghi, erbs["dhi"], albedo=cfg["albedo"])["poa_global"]
    return np.nan_to_num(np.asarray(poa, float))


def dc_power(poa: np.ndarray, t_air: np.ndarray, wind: Any, cfg: dict[str, Any]) -> np.ndarray:
    """DC power per kWp with the Faiman cell temperature."""
    t_cell = pvlib.temperature.faiman(poa, t_air, wind_speed=wind)
    return np.clip(poa / 1000.0 * (1 + cfg["gamma"] * (t_cell - 25.0)), 0, None)


def row_ac(pdc_h: np.ndarray, sr: np.ndarray, cfg: dict[str, Any]) -> np.ndarray:
    """pdc_h: (H,), sr: (n,) -> AC per row (n, H) in kW, clipped at the row's inverter share."""
    cap = cfg["row_kwp"] / cfg["dc_ac"]
    return np.minimum(cap, cfg["row_kwp"] * pdc_h[None, :] * sr[:, None] * cfg["inv_eff"])


def export_limit(cfg: dict[str, Any]) -> float:
    """Plant export limit of a capped contract [kW]."""
    return cfg["export_cap_frac"] * cfg["n_rows"] * cfg["row_kwp"] / cfg["dc_ac"]


def delivered(ac: np.ndarray, cfg: dict[str, Any], capped: bool) -> np.ndarray:
    """Plant output after the export limit, if there is one."""
    plant = ac.sum(0)
    if capped:
        return np.minimum(plant, export_limit(cfg))
    return plant
