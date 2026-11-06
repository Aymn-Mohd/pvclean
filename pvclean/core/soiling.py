"""Soiling and rain: row exposure, the daily dust process, rain recovery and the imperfect rain forecast."""
from __future__ import annotations
from typing import Any
import numpy as np


def exposure(cfg: dict[str, Any], site_seed: int | None = None, hetero: float = 1.0) -> np.ndarray:
    """Relative soiling exposure of each row: a front-to-back gradient with a random factor."""
    rng = np.random.default_rng(cfg["site_seed"] if site_seed is None else site_seed)
    n = cfg["n_rows"]
    grad = np.linspace(cfg["expo_front"], cfg["expo_back"], n)
    rnd = np.exp(rng.normal(0, cfg["expo_sigma"], n) - cfg["expo_sigma"] ** 2 / 2)
    e = grad * rnd
    e = e / e.mean()
    return np.clip(1.0 + hetero * (e - 1.0), cfg["expo_min"], None)


def dust(seed: int, cfg: dict[str, Any]) -> tuple[np.ndarray, np.ndarray]:
    """Site-level daily loss increment for a mean-exposure row, and the row noise. cfg season_shift moves the dust and storm seasons (a diagnostic option)."""
    rng = np.random.default_rng(seed + cfg["seed_offset_dust"])
    d = np.arange(365)
    shift = cfg.get("season_shift", 0)
    season = 1 + cfg["season_amp"] * np.sin(2 * np.pi * (d - cfg["dust_season_day"] - shift) / 365)
    cv = cfg["daily_cv"]
    ln = np.exp(rng.normal(0, np.sqrt(np.log(1 + cv ** 2)), 365) - np.log(1 + cv ** 2) / 2)
    inc = cfg["soil_mean"] * season * ln
    p_storm = cfg["storm_rate"] / 365 * (1 + cfg["storm_season_amp"] * np.sin(2 * np.pi * (d - cfg["storm_season_day"] - shift) / 365))
    storm = rng.random(365) < p_storm
    inc = inc + np.where(storm, rng.uniform(*cfg["storm_loss"], 365), 0.0)
    sd = cfg["row_noise_sd"]
    row_noise = np.exp(rng.normal(0, sd, (365, cfg["n_rows"])) - sd ** 2 / 2)
    return inc, row_noise


def expected_increment(cfg: dict[str, Any]) -> np.ndarray:
    """Expected site increment per day, without noise. It does not apply season_shift."""
    d = np.arange(365)
    season = 1 + cfg["season_amp"] * np.sin(2 * np.pi * (d - cfg["dust_season_day"]) / 365)
    p_storm = cfg["storm_rate"] / 365 * (1 + cfg["storm_season_amp"] * np.sin(2 * np.pi * (d - cfg["storm_season_day"]) / 365))
    return cfg["soil_mean"] * season + p_storm * np.mean(cfg["storm_loss"])


def rain_forecast(rain: np.ndarray, seed: int, cfg: dict[str, Any]) -> np.ndarray:
    """Imperfect forecast flag per day: is rain at or above the full-cleaning threshold expected?"""
    rng = np.random.default_rng(seed + cfg["seed_offset_rain_forecast"])
    big = rain >= cfg["rain_full_mm"]
    hit = rng.random(365) < cfg["rain_fc_hit"]
    false = rng.random(365) < cfg["rain_fc_false"]
    return np.where(big, hit, false)


def rain_recovery(mm: float, cfg: dict[str, Any]) -> float:
    """Share of the soiling a day's rain removes."""
    if mm >= cfg["rain_full_mm"]:
        return cfg["rain_full_recov"]
    if mm >= cfg["rain_light_mm"]:
        return cfg["rain_light_recov"]
    return 0.0
