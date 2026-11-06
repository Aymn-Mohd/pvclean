"""Planner inputs, built only from training seeds or training years."""
from __future__ import annotations
from typing import Any, Iterable
import numpy as np
import pandas as pd
from pvclean.markets import contract_value
from pvclean.weather import site_year, weather
from .plant import clear_sky


def input_seeds(cfg: dict[str, Any]) -> range:
    """Seeds of the planner inputs."""
    return range(cfg["input_seed_start"], cfg["input_seed_stop"])


def climatology_pdc(cfg: dict[str, Any], seeds: Iterable[int] | None = None) -> np.ndarray:
    """Mean hourly DC per kWp: the planner's production forecast. With cfg wx_site it is the mean over the real years cfg clim_years, which must be given."""
    if cfg.get("wx_site"):
        return np.nanmean([site_year(y, cfg)["pdc"] for y in cfg["clim_years"]], axis=0)
    seeds = input_seeds(cfg) if seeds is None else seeds
    acc = np.zeros(8760)
    for s in seeds:
        acc += weather(s, cfg)["pdc"]
    return acc / len(list(seeds))


def planner_inputs(contract: str, cfg: dict[str, Any], train_seeds: Iterable[int] | None = None) -> tuple[np.ndarray, np.ndarray, float]:
    """Production climatology, expected hourly value as a month x hour mean, and the constant production-weighted price of the econ baseline."""
    seeds = list(input_seeds(cfg) if train_seeds is None else train_seeds)
    clim = climatology_pdc(cfg, seeds)
    allv = np.array([contract_value(contract, s, cfg)[0] for s in seeds])
    q = cfg.get("vexp_q")
    if q:                       # winsorise heavy-tailed prices before averaging (training years only)
        pos = allv[allv > 0]
        if pos.size:
            allv = np.minimum(allv, np.quantile(pos, q))
    vals = allv.mean(axis=0)
    cs = clear_sky(cfg)
    df = pd.DataFrame(dict(m=cs["month"], h=cs["hour"], v=vals))
    vexp = df.groupby(["m", "h"]).v.transform("mean").values
    pbar = float((vexp * clim).sum() / clim.sum())
    return clim, vexp, pbar
