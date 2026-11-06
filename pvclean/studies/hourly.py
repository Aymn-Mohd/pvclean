"""Replay of real hourly prices with generated weather: leave-one-year-out, rolling origin, oracle inputs and forecast scenarios."""
from __future__ import annotations
from typing import Any
import numpy as np
from pvclean.stats import ci95, paired_short as paired
from .study import Study


def real(S: Study) -> dict[str, Any]:
    """AEMO leave-one-price-year-out (results_real.json)."""
    P = S.params; pols = P["policies"]; out: dict[str, Any] = {}
    with S.runner_pool() as rn:
        for mk in P["regions"]:
            for sh in P["shapes"]:
                for q in P["vexp_q"]:
                    cfgs = {}
                    for c in P["contracts"]:
                        folds = []
                        for k in range(3):
                            tr = tuple(i for i in range(3) if i != k)
                            over_tr = {"real_market": f"{mk}_{sh}", "real_years": tr, "vexp_q": q}
                            over_te = {"real_market": f"{mk}_{sh}", "real_years": (k,), "vexp_q": q}
                            best = rn.tune_params(c, cfg_over=over_tr, policies=pols)
                            folds.append(rn.evaluate_real(c, best, over_te, over_tr, pols))
                        cfgs[c] = folds
                    out[f"{mk}|{sh}|{q}"] = cfgs
    return out


def roll(S: Study) -> dict[str, Any]:
    """Rolling origin: tune and build planner inputs on the previous price year only (results_roll.json)."""
    P = S.params; pols = P["policies"]; out = {}
    with S.runner_pool() as rn:
        for mk in P["regions"]:
            for c in P["contracts"]:
                folds = []
                for k in (1, 2):
                    otr = {"real_market": f"{mk}_aligned", "real_years": (k - 1,)}; ote = {"real_market": f"{mk}_aligned", "real_years": (k,)}
                    best = rn.tune_params(c, cfg_over=otr, policies=pols)
                    folds.append(rn.evaluate_real(c, best, ote, otr, pols))
                out[f"{mk}|{c}"] = folds
    return out


def oracle(S: Study) -> dict[str, Any]:
    """The tuned parameters of the leave-one-year-out replay, with planner inputs from the test year (results_oracle.json)."""
    P = S.params; pols = P["policies"]; R = S.stored("results_real.json"); out = {}
    with S.runner_pool() as rn:
        for mk in P["regions"]:
            for c in P["contracts"]:
                folds = []
                for k in range(3):
                    best = {p: R[f"{mk}|aligned|None"][c][k][p]["params"] for p in pols}
                    folds.append(rn.evaluate_summary(c, best, cfg_over={"real_market": f"{mk}_aligned", "real_years": (k,)}, policies=pols))
                out[f"{mk}|{c}"] = folds
    return out


def spain(S: Study) -> dict[str, Any]:
    """OMIE replay: leave-one-year-out, rolling origin and oracle inputs (results_spain.json)."""
    P = S.params; pols = P["policies"]; mk = P["market"]; out: dict[str, Any] = {"loyo": {}, "roll": {}, "oracle": {}}
    with S.runner_pool() as rn:
        base = rn.baselines
        for c in P["contracts"]:
            lo, ro, orc = [], [], []
            for k in range(3):
                tr = tuple(i for i in range(3) if i != k)
                otr = {"real_market": mk, "real_years": tr}; ote = {"real_market": mk, "real_years": (k,)}
                best = rn.tune_params(c, cfg_over=otr, policies=pols)
                lo.append(rn.evaluate_real(c, best, ote, otr, pols))
                orc.append(rn.evaluate_summary(c, best, cfg_over=ote, policies=pols))
            for k in (1, 2):
                otr = {"real_market": mk, "real_years": (k - 1,)}; ote = {"real_market": mk, "real_years": (k,)}
                best = rn.tune_params(c, cfg_over=otr, policies=pols)
                ro.append(rn.evaluate_real(c, best, ote, otr, pols))
            for nm, folds in (("loyo", lo), ("roll", ro), ("oracle", orc)):
                pooled = {p: np.concatenate([f[p]["inc_net_seeds"] for f in folds]) for p in pols}
                bb = max(base, key=lambda p: pooled[p].mean())
                out[nm][c] = dict(best_baseline=bb, paired=paired(pooled["proposed"], pooled[bb]), noval=paired(pooled["proposed"], pooled["proposed_noval"]),
                                  proposed=float(pooled["proposed"].mean()), baseline=float(pooled[bb].mean()),
                                  per_fold=[float((np.array(f["proposed"]["inc_net_seeds"]) - np.array(f[bb]["inc_net_seeds"])).mean()) for f in folds],
                                  params=[{p: f[p]["params"] for p in pols} for f in folds])
    return out


def forecast(S: Study) -> dict[str, Any]:
    """Forecast-information hierarchy on real prices, leave-one-year-out (results_forecast.json)."""
    P = S.params; modes = P["modes"]; out = {}
    with S.runner_pool() as rn:
        base = rn.baselines
        for mk in P["markets"]:
            for c in P["contracts"]:
                per: dict[str, list] = {m: [] for m in modes}; bases = []
                for k in range(3):
                    tr = tuple(i for i in range(3) if i != k)
                    otr = {"real_market": mk, "real_years": tr}; ote = {"real_market": mk, "real_years": (k,)}
                    for m in modes:
                        pols = base + ["proposed"] if m == "clim" else ["proposed"]
                        best = rn.tune_params(c, cfg_over=dict(otr, fc_mode=m), policies=pols)
                        ev = rn.evaluate_real(c, best, dict(ote, fc_mode=m), dict(otr, fc_mode=m), pols)
                        per[m].append(ev["proposed"]["inc_net_seeds"])
                        if m == "clim":
                            bases.append({p: ev[p]["inc_net_seeds"] for p in base})
                pooled_b = {p: np.concatenate([b[p] for b in bases]) for p in base}
                bb = max(base, key=lambda p: pooled_b[p].mean())
                res: dict[str, Any] = dict(best_baseline=bb, baseline=float(pooled_b[bb].mean()))
                for m in modes:
                    d = np.concatenate(per[m]) - pooled_b[bb]
                    mm, h = ci95(d)
                    res[m] = dict(gain=mm, ci=h, wins=int((d > 0).sum()), n=len(d), value=float(np.concatenate(per[m]).mean()),
                                  per_fold=[float((np.array(per[m][i]) - np.array(bases[i][bb])).mean()) for i in range(3)])
                out[f"{mk}|{c}"] = res
    return out


def replay(S: Study) -> dict[str, Any]:
    """Real-market replay with scenarios F0 to F4. F1 reuses the F0 parameters with previous-year inputs (results_replay.json)."""
    P = S.params; modes = P["modes"]; out = {}
    with S.runner_pool() as rn:
        for mk in P["markets"]:
            for c in P["contracts"]:
                for k in range(3):
                    tr = tuple(i for i in range(3) if i != k)
                    otr = {"real_market": mk, "real_years": tr}; ote = {"real_market": mk, "real_years": (k,)}
                    res = {}
                    for name, m in modes.items():
                        extra = dict(fc_mode=m, roll_min_hist=1)
                        pols = (rn.baselines if name == "F0" else []) + ["proposed", "ft"]
                        best = rn.tune_params(c, cfg_over=dict(otr, **extra), policies=pols)
                        ev = rn.evaluate_real(c, best, dict(ote, **extra), dict(otr), pols)
                        res[name] = {p: dict(params=ev[p]["params"], seeds=ev[p]["inc_net_seeds"], n_clean=ev[p]["n_clean"][0]) for p in pols}
                        if name == "F0" and k >= 1:
                            pv = ["econ", "proposed", "ft"]
                            ev1 = rn.evaluate_real(c, {p: best[p] for p in pv}, dict(ote, fc_mode="clim", roll_min_hist=1), {"real_market": mk, "real_years": (k - 1,)}, pv)
                            res["F1"] = {p: dict(params=ev1[p]["params"], seeds=ev1[p]["inc_net_seeds"], n_clean=ev1[p]["n_clean"][0]) for p in pv}
                    out[f"{mk}|{c}|{k}"] = res
    return out
