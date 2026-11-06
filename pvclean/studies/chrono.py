"""Chronological real-market replay with interval-level valuation.

Folds: Y2 tunes on year 1 and tests year 2 (parameters frozen). Y3 tunes on years 1 and 2 and tests year 3. Y3frozen uses year-1 parameters and inputs on year 3. Every policy is tuned
on the training years with the train seeds; the best baseline is selected by training mean only. Planner inputs at test time come from the training years only."""
from __future__ import annotations
from typing import Any
import numpy as np
from pvclean.forecasts import DEPLOYABLE
from pvclean.stats import decomp, paired, tally_rule
from .runner import Runner, record_job
from .study import Study

CONTRACTS = ["merchant", "ppa"]
FC = ["proposed", "ft"]
MODES = {"F2": "roll", "CLIM": "clim", "F3": "dayahead", "F4": "perfect"}
FOLDS = {"Y2": ((0,), (1,)), "Y3": ((0, 1), (2,))}
MAIN = ["SA1_aligned", "QLD1_aligned", "ES_raw"]
SENS = ["SA1_raw", "QLD1_raw"]


def run_fold(rn: Runner, mk: str, c: str, fold: str, tuned_y1: dict[str, Any] | None = None, extra: dict[str, Any] | None = None, modes: dict[str, str] = MODES) -> dict[str, Any]:
    """One market x contract x fold: tuned parameters, per-seed test records per forecast, and comparisons. extra applies to every tuning, test and v_ref run."""
    extra = extra or {}
    tr, te = ((0,), (2,)) if fold == "Y3frozen" else FOLDS[fold]
    rec: dict[str, Any] = dict(market=mk, contract=c, fold=fold, train_years=tr, test_years=te,
                               label=("MAIN" if mk in MAIN else "SENSITIVITY") + ("" if fold != "Y3frozen" else " (secondary)"),
                               f3_note="real day-ahead" if mk.startswith("ES") else "proxy: operating-day realised RT prices (no day-ahead market)", tuned={}, test={})
    base = rn.baselines
    for name, mode in modes.items():
        ex = dict(real_value=mk, fc_mode=mode, roll_min_hist=1, **extra)
        otr = dict(ex, real_years=tr); ote = dict(ex, real_years=te)
        pols = (base if name == "F2" else []) + FC
        best = {p: tuned_y1[name][p] for p in pols} if fold == "Y3frozen" else rn.tune(c, otr, pols)
        rec["tuned"][name] = best
        rec["test"][name] = rn.evaluate(c, {p: best[p]["params"] for p in pols}, ote, otr, pols)
    bb = max(base, key=lambda p: rec["tuned"]["F2"][p]["train_mean"])
    rec["best_baseline"] = bb
    rec["vref"] = rn.map(record_job, [("vref", c, s, dict(real_value=mk, real_years=te, **extra)) for s in rn.test])
    t = rec["test"]
    rec["cmp"] = {f"planner-ft|{n}": paired(t[n]["proposed"]["net"], t[n]["ft"]["net"]) for n in modes}
    rec["cmp"]["planner-bestbase|F2"] = paired(t["F2"]["proposed"]["net"], t["F2"][bb]["net"])
    rec["cmp"]["ft-bestbase|F2"] = paired(t["F2"]["ft"]["net"], t["F2"][bb]["net"])
    rec["cmp"]["planner-econ|F2"] = paired(t["F2"]["proposed"]["net"], t["F2"]["econ"]["net"])
    return rec


def verdict(res: dict[str, Any], markets: list[str] = MAIN, folds: tuple[str, ...] = ("Y2", "Y3")) -> dict[str, Any]:
    """H-R1 and H-R3 rule over market x contract x fold."""
    return tally_rule(res[f"{mk}|{c}|{f}"]["cmp"]["planner-ft|F2"] for mk in markets for c in CONTRACTS for f in folds)


def chrono(S: Study) -> dict[str, Any]:
    """R1 replay (results_chrono.json)."""
    out: dict[str, Any] = {"_meta": dict(train_seeds=S.protocol.train, test_seeds=S.protocol.test, modes=MODES, workers=S.protocol.workers,
                                         deployable={n: DEPLOYABLE.get(n, True) for n in MODES})}
    with S.runner_pool() as rn:
        for mk in MAIN + SENS:
            for c in CONTRACTS:
                for fold in ("Y2", "Y3", "Y3frozen"):
                    out[f"{mk}|{c}|{fold}"] = run_fold(rn, mk, c, fold, tuned_y1=out.get(f"{mk}|{c}|Y2", {}).get("tuned"))
    out["_verdict_H_R1"] = verdict(out)
    out["_verdict_secondary_Y3frozen"] = verdict(out, folds=("Y2", "Y3frozen"))
    out["_sensitivity_raw_calendar"] = verdict(out, markets=SENS)
    out["_sensitivity_raw_calendar"]["note"] = "SENSITIVITY: 2 markets x 2 contracts x 2 years = 8 case-years; the 10/12 and 6/12 thresholds do not apply"
    return out


def rq1_decomposition(S: Study) -> dict[str, Any]:
    """Revenue, energy and cost decomposition of the generated-market RQ1 and of every R1 case-year (results_rq1_decomp.json). The rerun must reproduce results.json to 1e-6."""
    pols = S.params["policies"]; ref = S.stored("results.json")["rq1"]; res: dict[str, Any] = {}; check: dict[str, Any] = {}
    with S.runner_pool() as rn:
        for c in rn.contracts:
            best = rn.tune(c, {}, pols)
            ev = rn.evaluate(c, {p: best[p]["params"] for p in pols}, {}, {}, pols)
            vref = rn.map(record_job, [("vref", c, s, {}) for s in rn.test])
            for p in pols:
                if p in ref[c]:
                    m = float(np.mean(ev[p]["inc_net"])); r = ref[c][p]["inc_net"][0]
                    check[f"{c}|{p}"] = dict(rerun=m, stored=r, abs_diff=abs(m - r), params_equal=ev[p]["params"] == ref[c][p]["params"])
            bb = max(rn.baselines, key=lambda p: best[p]["train_mean"])
            res[c] = dict(tuned=best, test=ev, vref=vref, best_baseline_train=bb, best_baseline_stored_test_selected=ref[c].get("_best_baseline"),
                          decomp={"planner-ft": decomp(ev["proposed"], ev["ft"], vref), "planner-bestbase": decomp(ev["proposed"], ev[bb], vref), "ft-bestbase": decomp(ev["ft"], ev[bb], vref)})
    worst = max(v["abs_diff"] for v in check.values())
    out: dict[str, Any] = dict(rq1_reproduction=dict(max_abs_diff=worst, tol=1e-6, ok=bool(worst <= 1e-6), per_policy=check))
    if worst > 1e-6:
        raise SystemExit("STOP: RQ1 rerun does not reproduce results.json rq1 inc_net to 1e-6")
    out["rq1"] = res
    ch = S.stored("results_chrono.json"); r1 = {}
    for key, rec in ch.items():
        if not key.startswith("_"):
            t = rec["test"]["F2"]; bb = rec["best_baseline"]
            r1[key] = dict(label=rec["label"], best_baseline=bb, decomp={"planner-ft": decomp(t["proposed"], t["ft"], rec["vref"]), "planner-bestbase": decomp(t["proposed"], t[bb], rec["vref"])})
    out["r1"] = r1
    return out
