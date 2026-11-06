"""Phase R1b stage 4 (ANALYSIS, from existing results only): paired absolute gaps J* - J of the exact benchmark.
J* = clairvoyant optimum per instance (results_exact.json 'exact', seeds 0-19); J = receding-horizon MILP arms (results_horizon.json),
tuned site-information policies (results_exact.json 'site') and FT (results_matched.json part_b), all as gain over no cleaning (USD
per 60-day instance) on the same seeds. Reports per setting: mean gap with 95% paired t-interval, the ratio of means
100 mean(J) / mean(J*) (what table_exact.tex prints), the mean of per-instance ratios (instances with J* > 1 USD only), and solver
statistics. Writes results/milp_gaps.json."""
from __future__ import annotations
from typing import Any
import numpy as np
from scipy import stats
from .study import Study

SET = ["fixed|c4.0", "fixed|c12.0", "merchant|c4.0", "merchant|c12.0"]


def ci(d: Any) -> Any:
    """Mean and 95% t limits."""
    d = np.asarray(d, float); m = float(d.mean()); h = float(stats.t.ppf(0.975, len(d) - 1) * d.std(ddof=1) / np.sqrt(len(d)))
    return dict(mean=m, lo=m - h, hi=m + h)


def run(S: Study) -> dict:
    """Paired gaps to the clairvoyant optimum, from stored results (milp_gaps.json)."""
    ex = S.stored("results_exact.json"); mp = S.stored("results_matched.json")
    hz = S.stored("results_horizon.json")
    out = {}
    for k in SET:
        c, cr = k.split("|"); crow = float(cr[1:])
        e = sorted(ex[k]["exact"], key=lambda x: x["seed"]); js = np.array([x["opt"] for x in e]); seeds = [x["seed"] for x in e]
        J = {p: np.array(ex[k]["site"][p]["seeds"]) for p in ("fixed", "threshold", "econ", "proposed")}
        J["ft"] = np.array(mp["part_b"][k]["ft"]["seeds"])
        solv = {}
        for arm in sorted({x["arm"] for x in hz if x["contract"] == c and x["crow"] == crow}):
            runs = {x["seed"]: x for x in hz if x["contract"] == c and x["crow"] == crow and x["arm"] == arm}
            J["MILP " + arm] = np.array([runs[s]["gain"] for s in seeds])
            st = {}
            for x in runs.values():
                for s_, n_ in x["status_counts"].items(): st[s_] = st.get(s_, 0) + n_
            solv["MILP " + arm] = dict(runs=len(runs), solves=int(sum(x["n_solves"] for x in runs.values())), status_counts=st,
                                       no_solution=int(sum(x["no_solution"] for x in runs.values())),
                                       max_mip_gap=max((x["max_gap"] or 0.0) for x in runs.values()),
                                       max_solve_s=max(x["max_solve_s"] for x in runs.values()),
                                       mean_run_s=float(np.mean([x["runtime"] for x in runs.values()])),
                                       violations=int(sum(x["viol"] for x in runs.values())))
        pos = js > 1.0
        rows = {}
        for p, j in J.items():
            rows[p] = dict(gap_usd=ci(js - j), mean_J=float(j.mean()), ratio_of_means_pct=float(100 * j.mean() / js.mean()),
                           mean_of_ratios_pct=float(100 * np.mean(j[pos] / js[pos])) if pos.any() else None, n_ratio=int(pos.sum()))
        out[k] = dict(n=len(js), jstar_mean=float(js.mean()), jstar_min=float(js.min()), jstar_le_1usd=int((~pos).sum()),
                      clairvoyant=dict(status=sorted({x["status"] for x in e}), max_mip_gap=float(max(x["gap"] for x in e)),
                                       runtime="not stored in results_exact.json"),
                      rows=rows, solver=solv)
    return dict(label="ANALYSIS", settings=out)
