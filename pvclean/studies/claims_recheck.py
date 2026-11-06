"""Phase R1b stage 2 (ANALYSIS): recheck of every sensitivity result the paper cites, from per-seed results.

Settings (generated markets unless noted; planner minus the best baseline as stored, i.e. as the paper cites it):
  price-dip scan   results.json price, merchant and ppa at price_depress_scale 0, 1, 1.5, 2, 3
  real Dubai wx    results_wx.json, fixed, merchant, ppa (48 held-out seeds: 16 weather years x 3 dust draws)
  NREL soiling     results_nrel.json med and p90, fixed and merchant
  cleaning cost    results_extra.json cost, c_row 24 (mid) and 48 (manual), fixed and merchant
results_wx.json and results_nrel.json store per-seed values and are read as stored. results.json price and results_extra.json cost
store only paired summaries, so those settings are rerun here with per-seed storage (same grids, seeds and tuning as the original
scripts, via chrono_replay.tune/evaluate); the rerun must reproduce the stored paired mean to 1e-6, otherwise the script stops.
The best baseline of the stored results was selected on the TEST mean; the rerun also reports the training-selected one.
Per row: paired mean, 95% t-interval, whether it excludes 0, two-sided Wilcoxon signed-rank p, wins out of n, and what the paper
says about significance. Writes results/claims_recheck.json."""
from __future__ import annotations
from typing import Any
from pvclean.stats import ci95
import time
import numpy as np
from scipy import stats
from .study import Study

# what the paper text says (main.tex sec. Regimes and Sensitivity, supplement.tex); None = no significance statement
PAPER = {"price|merchant|k1.5": "significant", "price|ppa|k1.5": "significant",
         "price|merchant|k3.0": "not significant", "price|ppa|k3.0": "not significant",
         "wx|merchant": "significant", "wx|ppa": "significant", "wx|fixed": "not significant",
         "nrel|med|fixed": "not significant", "nrel|med|merchant": "not significant",
         "cost|fixed|c24.0": "not significant", "cost|fixed|c48.0": "not significant",
         "cost|merchant|c24.0": "significant", "cost|merchant|c48.0": "significant"}


def row(d: Any, key: Any, source: Any, bb: Any, extra: Any = None) -> Any:
    """One row of the recheck: interval, Wilcoxon test and agreement with the paper text."""
    d = np.asarray(d, float)
    m, h = ci95(d)
    nz = d[d != 0]
    p = float(stats.wilcoxon(nz).pvalue) if len(nz) > 0 else 1.0
    excl = bool(m - h > 0 or m + h < 0)
    claim = PAPER.get(key)
    agree = None if claim is None else (excl == (claim == "significant"))
    out = dict(key=key, source=source, best_baseline=bb, mean=m, ci=h, lo=m - h, hi=m + h, excludes_0=excl, wilcoxon_p=p,
               wins=int((d > 0).sum()), n=len(d), paper_says=claim, paper_agrees=agree)
    out.update(extra or {})
    return out


def rerun(rn: Any, c: Any, over: Any, pols: Any, stored: Any) -> Any:
    """Reruns one cell with per-seed storage and compares it with the stored mean."""
    BASE = rn.baselines
    best = rn.tune(c, over, pols)
    ev = rn.evaluate(c, {p: best[p]["params"] for p in pols}, over, {}, pols)
    bb = max(BASE, key=lambda p: np.mean(ev[p]["inc_net"]))
    d = np.array(ev["proposed"]["inc_net"]) - np.array(ev[bb]["inc_net"])
    bbt = max(BASE, key=lambda p: best[p]["train_mean"])
    dt = np.array(ev["proposed"]["inc_net"]) - np.array(ev[bbt]["inc_net"])
    diff = abs(float(d.mean()) - stored["mean"])
    return d, bb, dict(stored_mean=stored["mean"], stored_ci=stored["ci"], repro_abs_diff=diff, bb_train=bbt,
                       train_selected=dict(zip(("mean", "ci"), ci95(dt))), params={p: best[p]["params"] for p in pols},
                       seeds={p: ev[p]["inc_net"] for p in pols})


def run(S: Study) -> dict:
    """Rechecks every cited sensitivity result (claims_recheck.json)."""
    t0 = time.time()
    res = S.stored("results.json")
    X = S.stored("results_extra.json")
    WX = S.stored("results_wx.json")
    NR = S.stored("results_nrel.json")
    rows = []
    with S.runner_pool() as rn:
        for c in ["merchant", "ppa"]:
            for k in S.params["price_scales"]:
                st = res["price"][f"{c}|k{k}"]
                d, bb, ex = rerun(rn, c, {"price_depress_scale": k}, ["fixed", "threshold", "econ", "proposed", "proposed_noval"], st["vs_best"])
                ex["neg_hours_pct"] = st["stats"]["neg_all"] * 100
                rows.append(row(d, f"price|{c}|k{k}", "results.json price (rerun per seed)", bb, ex))
                print(rows[-1]["key"], bb, round(rows[-1]["mean"], 2), "repro", ex["repro_abs_diff"], round(time.time() - t0), flush=True)
        for c in ["fixed", "merchant"]:
            for crow in [24.0, 48.0]:
                st = X["cost"][f"{c}|c{crow}"]
                d, bb, ex = rerun(rn, c, {"c_row": crow}, ["fixed", "threshold", "econ", "proposed"], st["paired"])
                rows.append(row(d, f"cost|{c}|c{crow}", "results_extra.json cost (rerun per seed)", bb, ex))
                print(rows[-1]["key"], bb, round(rows[-1]["mean"], 2), "repro", ex["repro_abs_diff"], round(time.time() - t0), flush=True)
    for c in ["fixed", "merchant", "ppa"]:
        r = WX[c]; bb = r["best_baseline"]
        d = np.array(r["seeds"]["proposed"]) - np.array(r["seeds"][bb])
        rows.append(row(d, f"wx|{c}", "results_wx.json (stored per seed)", bb, dict(stored_mean=r["paired"]["mean"], repro_abs_diff=abs(d.mean() - r["paired"]["mean"]))))
    for tag in ["med", "p90"]:
        for c in ["fixed", "merchant"]:
            r = NR[f"{tag}|{c}"]; bb = r["best_baseline"]
            d = np.array(r["seeds"]["proposed"]) - np.array(r["seeds"][bb])
            rows.append(row(d, f"nrel|{tag}|{c}", "results_nrel.json (stored per seed)", bb, dict(stored_mean=r["paired"]["mean"], repro_abs_diff=abs(d.mean() - r["paired"]["mean"]), over=r["over"])))
    worst = max(r["repro_abs_diff"] for r in rows)
    out = dict(label="ANALYSIS", rows=rows, max_repro_abs_diff=worst, tol=1e-6, runtime_s=time.time() - t0,
               note="comparison: proposed minus the best baseline selected on the test mean, as stored and cited; train-selected in rows[*].train_selected for reruns")
    S.write(out)
    if worst > 1e-6:
        raise SystemExit(f"STOP: per-seed rerun does not reproduce the stored means (max |diff| {worst})")
    return out
