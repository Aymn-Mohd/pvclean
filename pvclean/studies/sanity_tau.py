"""Phase R1 ANALYSIS: single-row sanity check of the planner against the square-root cleaning interval.

One row, constant price (fixed tariff), 8 productive hours a day at constant output, no rain, no storms, no day-to-day or row
noise, no access windows, c_mission = 0, perfect state information. The soiling ratio falls by s per day, so the value lost per
day grows linearly with time since cleaning, L(t) = a t with a = tariff * kWh_day * s, and the average cost per day of cleaning
every tau days is (c + a tau^2 / 2) / tau, minimised at tau* = sqrt(2 c / a). The planner's index phi = g tau - A - c_row with
g = a t, A = a t (t - 1) / 2 cleans at the first t with a t (t + 1) / 2 >= c, i.e. t ~ tau* - 1/2: the measured interval should
approach tau* (within one day). Writes results/results_sanity_tau.json."""
from __future__ import annotations
from typing import Any
from pvclean import model
from pvclean.core.world import World
import numpy as np
from .study import Study

C_ROW = 4.0
TAU_TARGET = (7.3, 15.7, 41.2)      # non-integer so that rounding to whole days is visible


def setup() -> Any:
    """One row, 8 productive hours a day at constant output."""
    cfg = dict(model.CONFIG, n_rows=1, d0=0, d1=365, c_row=C_ROW, c_mission=0.0, blackouts=(), dc_ac=1.0, row_kwp=25.0, sr_floor=0.0)
    pdc = np.zeros(8760)
    for d in range(365):
        pdc[d * 24 + 8:d * 24 + 16] = 0.5
    kwh_day = 8 * cfg["row_kwp"] * 0.5 * cfg["inv_eff"]
    return cfg, pdc, kwh_day


def run_one(a: Any) -> Any:
    """Measures the cleaning interval at one loss slope."""
    cfg, pdc, kwh_day = setup()
    s = a / (cfg["tariff"] * kwh_day)
    w = World(weather=lambda seed, cfg: dict(pdc=pdc, rain=np.zeros(365), clear_pdc=None), dust=lambda seed, cfg: (np.full(365, s), np.ones((365, 1))),
              exposure=lambda cfg, site_seed=None, hetero=1.0: np.ones(1), rain_forecast=lambda rain, seed, cfg: np.zeros(365, bool))
    r = model.simulate("proposed", {"beta": 0.0, "kappa": 0.0}, "fixed", 0, info="perfect", cfg=cfg, clim=pdc, vexp=np.full(8760, cfg["tariff"]), pbar=cfg["tariff"], world=w)
    days = [d for d, _ in r["sched"]]
    gaps = np.diff([0] + days)            # day 0 starts clean
    tau_star = float(np.sqrt(2 * C_ROW / a))
    t_disc = int(np.ceil((-1 + np.sqrt(1 + 8 * C_ROW / a)) / 2))      # first t with a t (t + 1) / 2 >= c
    return dict(a=a, soil_per_day=s, tau_star=tau_star, tau_discrete_rule=t_disc, measured_mean=float(gaps.mean()),
                measured_median=float(np.median(gaps)), n_cleanings=len(days), gaps=gaps.tolist(),
                rel_err=float(gaps.mean() / tau_star - 1))


def cases() -> Any:
    """One run per target interval."""
    return [run_one(2 * C_ROW / t ** 2) for t in TAU_TARGET]


def run(S: Study) -> dict:
    """Writes results_sanity_tau.json."""
    return dict(c_row=C_ROW, cases=cases())
