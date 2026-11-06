"""Phase R3 UNREGISTERED DIAGNOSTICS, run after the pre-registered replay to check its surprises. Nothing here enters the H-R3 verdict or
results/results_matched.json. Writes results/r3_checks.json.

  soil     no-cleaning soiling loss per site and test year (energy against a dust-free run), and rain timing inside the dust half-year
  r1wx     the same soiling and rain figures for R1's synthetic Dubai weather, over the 50 test seeds
  stored   stored data: every policy against no cleaning; planner against the realised best baseline; planner's kappa at the grid edge
  shift    the full replay with the dust and storm seasons moved by 182 days (season_shift): does season timing drive the site contrast?
  retune   the H-R3 tally with tuning repeated on other train seeds, to size the tuning noise around the 6-of-12 boundary"""
from __future__ import annotations
from typing import Any
from pvclean import model
from pvclean.stats import paired
from .chrono import CONTRACTS, run_fold
from .matched import CAL, FOLD_NAMES, MARKETS, SITES, SOIL, fold_test_year, site_over
from .runner import record_job
import time
import numpy as np
from .study import Study

POLS = ("fixed", "threshold", "econ", "ft", "proposed")
CASES = [(mk, c, f) for mk in MARKETS for c in CONTRACTS for f in FOLD_NAMES]


def row(rec: Any) -> Any:
    """Compact record of one case: paired comparisons, tuned parameters, value of cleaning per policy."""
    t = rec["test"]["F2"]; none = np.mean(t["none"]["net"])
    return dict(cmp={k: rec["cmp"][k] for k in ("planner-ft|F2", "planner-bestbase|F2")}, best_baseline=rec["best_baseline"],
                params={p: rec["tuned"]["F2"][p]["params"] for p in POLS}, none_net=float(none),
                voc={p: float(np.mean(t[p]["net"]) - none) for p in POLS}, row_cleanings={p: float(np.mean(t[p]["n_clean"])) for p in POLS})


def tally(rows: Any) -> Any:
    """Counts over the case-years."""
    m = [r["cmp"]["planner-ft|F2"] for r in rows.values()]
    return dict(mean_pos=sum(x["mean"] > 0 for x in m), mean_nonpos=sum(x["mean"] <= 0 for x in m), ci_wholly_below=sum(x["hi"] < 0 for x in m),
                ci_wholly_above=sum(x["lo"] > 0 for x in m))


def part_soil(rn: Any) -> Any:
    """No-cleaning soiling loss and rain timing per site and test year."""
    out = {}
    for mk in MARKETS:
        for fold in FOLD_NAMES:
            y = fold_test_year(fold); yi = CAL.index(y)
            base = dict(site_over(mk, y), real_value=mk, real_years=(yi,), fc_mode="roll", roll_min_hist=1)
            jobs = [("none", {}, "merchant", s, "site", 0.01, 1.0, o) for o in (base, dict(base, soil_mean=0.0, storm_rate=0.0)) for s in rn.test]
            r = rn.map(record_job, jobs)
            n = len(rn.test); dirty = np.mean([x["energy_kwh"] for x in r[:n]]); clean = np.mean([x["energy_kwh"] for x in r[n:]])
            a = model.site_year(y, dict(model.CONFIG, **SITES[mk])); rain = a["rain"]
            big = np.flatnonzero(rain >= model.CONFIG["rain_full_mm"])
            gaps = np.diff(np.r_[-1, big, len(rain)]) - 1
            d = np.arange(len(rain)); dusty = np.sin(2 * np.pi * (d - 75) / 365) > 0
            out[f"{mk}|{y}"] = dict(soiling_loss_pct=float(100 * (1 - dirty / clean)), longest_gap_5mm_days=int(gaps.max()), days_5mm=int(len(big)),
                                    days_5mm_dust_half=int((rain[dusty] >= 5).sum()), days_5mm_other_half=int((rain[~dusty] >= 5).sum()))
    return out


def part_r1wx(rn: Any) -> Any:
    """The same figures for the generated Dubai weather."""
    r = rn.map(record_job, [("none", {}, "merchant", s, "site", 0.01, 1.0, o) for o in ({}, dict(soil_mean=0.0, storm_rate=0.0)) for s in rn.test])
    n = len(rn.test); dirty = np.mean([x["energy_kwh"] for x in r[:n]]); clean = np.mean([x["energy_kwh"] for x in r[n:]])
    w = [model.weather(s, model.CONFIG) for s in rn.test]
    gaps = [int((np.diff(np.r_[-1, np.flatnonzero(a["rain"] >= 5), 365]) - 1).max()) for a in w]
    return dict(soiling_loss_pct=float(100 * (1 - dirty / clean)), dc_kwh_kwp=float(np.mean([a["pdc"].sum() for a in w])), rain_days_1mm=float(np.mean([(a["rain"] >= 1).sum() for a in w])),
                rain_days_5mm=float(np.mean([(a["rain"] >= 5).sum() for a in w])), longest_gap_5mm_days=float(np.mean(gaps)))


def part_stored(S: Any) -> Any:
    """Each policy against no cleaning, from stored data."""
    r3 = S.stored("results_matched.json")["r3"]; out = {}
    for k, v in r3.items():
        t = v["test"]["F2"]; none = np.array(t["none"]["net"])
        best = max(("fixed", "threshold", "econ"), key=lambda p: np.mean(t[p]["net"]))
        out[k] = dict(voc={p: float(np.mean(np.array(t[p]["net"]) - none)) for p in POLS}, realised_best_baseline=best,
                      planner_minus_realised_best=paired(t["proposed"]["net"], t[best]["net"]), planner_minus_none=paired(t["proposed"]["net"], none),
                      ft_minus_none=paired(t["ft"]["net"], none), kappa=v["tuned"]["F2"]["proposed"]["params"]["kappa"],
                      d_row_cleanings=v["decomp"]["planner-ft"]["d_row_cleanings"]["mean"])
    return out


def part_replay(rn: Any, soil: Any, extra: Any) -> Any:
    """The replay with extra overrides."""
    rows = {}
    for mk, c, f in CASES:
        ex = dict(site_over(mk, fold_test_year(f), SOIL[soil]), **extra)
        rows[f"{mk}|{c}|{f}"] = row(run_fold(rn, mk, c, f, extra=ex))
    return dict(rows=rows, tally=tally(rows))


def run(S: Study) -> dict:
    """All parts (r3_checks.json)."""
    P = S.params; shift_days = P["shift_days"]; retune = P["retune"]; out = {}; t0 = time.time()
    with S.runner_pool() as rn:
        out["soil"] = part_soil(rn)
        out["r1wx"] = part_r1wx(rn)
        out["stored"] = part_stored(S)
        out["shift"] = {soil: part_replay(rn, soil, dict(season_shift=shift_days)) for soil in SOIL}
        out["retune"] = {name: part_replay(rn.with_(train=seeds), "soil0.30", {}) for name, seeds in retune.items()}
    out["_meta"] = dict(label="UNREGISTERED DIAGNOSTIC", shift_days=shift_days, retune=retune, workers=S.protocol.workers, runtime_s_last=time.time() - t0)
    return out
