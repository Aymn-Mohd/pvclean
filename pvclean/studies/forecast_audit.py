"""EXP-07: forecast scenarios F0-F4 on real price years: error metrics and an automated no-lookahead (poison) audit.
Writes results/results_forecast_audit.json. Metrics are over the planning horizon (7 days) of each daily decision, daylight hours only
(clim production > 0.05 kW/kWp), contract value in USD/kWh."""
from __future__ import annotations
from typing import Any
from pvclean import model
from pvclean.data import data_path
from pvclean.forecasts import info_cutoff, value_forecast
import numpy as np
from .study import Study

MARKETS = ["SA1_aligned", "QLD1_aligned", "ES_raw"]
CONTRACTS = ["merchant", "ppa"]
H = 168


def scenario_modes(k: Any) -> Any:
    """Forecast scenarios of one test year; F1 needs a previous year."""
    m = {"F0": "clim", "F2": "roll", "F3": "dayahead", "F4": "perfect"}
    if k >= 1: m["F1"] = "clim"
    return m


def audit() -> Any:
    """Error metrics and the no-lookahead audit."""
    npz = np.load(data_path("real_prices.npz"))
    out = {"metrics": [], "leakage": {}}
    clim = model.climatology_pdc(dict(model.CONFIG))
    n_checked = 0; n_fail = 0
    for mk in MARKETS:
        for c in CONTRACTS:
            for k in range(3):
                tr0 = tuple(i for i in range(3) if i != k)
                spot = npz[mk][k]; val = model.hourly_value(c, spot)
                for name, mode in scenario_modes(k).items():
                    yrs = (k - 1,) if name == "F1" else tr0
                    cfg = dict(model.CONFIG, real_market=mk, real_years=yrs)
                    _, vexp, _ = model.planner_inputs(c, cfg)
                    E = []; W = []; RW = []; NEG = []; ALL = []
                    for d in range(1, 358):
                        hh = np.arange(d * 24, d * 24 + H)
                        f = value_forecast(mode, d, hh, val, vexp, min_hist=1)
                        # leakage audit: poison everything the provider is not entitled to see
                        cut = info_cutoff(mode, d, H)
                        pv = val.copy(); pv[cut:] = np.nan
                        if mode != "perfect":
                            f2 = value_forecast(mode, d, hh, pv, vexp, min_hist=1)
                            n_checked += 1
                            if not (np.isfinite(f2).all() and np.allclose(f, f2)): n_fail += 1
                        e = f - val[hh]; day = clim[hh] > 0.05
                        E.append(e[day]); W.append(clim[hh][day]); RW.append((clim[hh] * val[hh])[day]); ALL.append(np.abs(e))
                        neg = (spot[hh] < 0) & day
                        if neg.any(): NEG.append(np.abs(e[neg]))
                    E = np.concatenate(E); W = np.concatenate(W); RW = np.concatenate(RW)
                    neg = np.concatenate(NEG) if NEG else np.array([np.nan])
                    out["metrics"].append(dict(market=mk, contract=c, year=k, scenario=name, mae=float(np.abs(E).mean()),
                                               rmse=float(np.sqrt((E ** 2).mean())), bias=float(E.mean()),
                                               mae_prod_w=float((np.abs(E) * W).sum() / W.sum()),
                                               mae_rev_w=float((np.abs(E) * RW).sum() / RW.sum()) if RW.sum() > 0 else None,
                                               mae_neg_hours=float(np.nanmean(neg)), n_neg=int(np.isfinite(neg).sum()) if NEG else 0,
                                               mae_all_hours=float(np.concatenate(ALL).mean())))
    out["leakage"] = dict(checks=n_checked, failures=n_fail, rule="forecast recomputed with realised values at/after information_cutoff set to NaN; must be finite and identical")
    return out


def run(S: Study) -> dict:
    """Writes results_forecast_audit.json."""
    return audit()
