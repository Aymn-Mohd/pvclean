"""Phase R2 (EXTENSION, pre-registered in docs/EXPERIMENT_LOG.md "Phase R2"): robot-capability sweep on the generated markets.

One factor varies at a time from sim.CONFIG; the default setting is shared by all five factors, so the sweep has 11 settings x 4
contracts. Every policy (fixed, threshold, econ, ft, proposed) is retuned on the train seeds in every cell with the RQ1 grids, and the best
conventional baseline (fixed, threshold, econ) is picked on the training mean of that cell. Test: the 50 test seeds, per-seed records.
The default cell must reproduce results/results_rq1_decomp.json rq1 exactly; otherwise the script stops before the H-R2 rule.

H-R2 rule, per tight setting (night240, service40, battery6) and contract: paired over seeds,
  diff_s = (planner - bestbase)_tight,s - (planner - bestbase)_default,s, with the mean and 95% t-interval.
SUPPORTED if the interval lies wholly above 0 in >= 6 of 12 cells and wholly below 0 in none; NOT SUPPORTED if the mean is <= 0 in
>= 6; PARTIAL otherwise.

Writes results_robot.json."""
from __future__ import annotations
from typing import Any
from pvclean import model
from pvclean.stats import interval_rule, paired
from .runner import KEEP
import time
import numpy as np
from .study import Study

def rows_per_night(over: Any) -> Any:
    """Rows one mission can clean when it reaches the far end of the plant (a capacity scale for reporting only)."""
    cfg = dict(model.CONFIG, **over)
    far = 2 * cfg["row_pitch_m"] * cfg["n_rows"] / cfg["speed_mps"] / 60.0
    k = min(cfg["n_rows"], int((cfg["night_min"] - far) // cfg["service_min"]))
    return k if cfg.get("battery_rows") is None else min(k, cfg["battery_rows"])


def cell(rn: Any, setting: Any, over: Any, c: Any, POLS: Any) -> Any:
    """One setting and contract: retune every policy, test, and collect the metrics."""
    best = rn.tune(c, over, POLS)
    test = rn.evaluate(c, {p: best[p]["params"] for p in POLS}, over, {}, POLS)
    bb = max(rn.baselines, key=lambda p: best[p]["train_mean"])
    none = test["none"]
    pl = test["proposed"]
    zero = np.zeros(len(rn.test))
    metrics = dict(value_of_cleaning=paired(pl["net"], none["net"]),
                   planner_bestbase=paired(pl["net"], test[bb]["net"]),
                   planner_ft=paired(pl["net"], test["ft"]["net"]),
                   recovered_mwh=paired((np.array(pl["energy_kwh"]) - none["energy_kwh"]) / 1000.0, zero),
                   row_cleanings=paired(pl["n_clean"], zero), missions=paired(pl["n_missions"], zero))
    return dict(setting=setting, contract=c, over=over, rows_per_night=rows_per_night(over), tuned=best, test=test,
                best_baseline=bb, metrics=metrics)


def check_default(out: Any, D: Any, contracts: Any, POLS: Any) -> Any:
    """Exact per-seed equality of the default cells with the stored R1 RQ1 rerun."""
    for c in contracts:
        t = out[f"default|{c}"]["test"]
        for p in ["none"] + POLS:
            for k in KEEP:
                if t[p][k] != D[c]["test"][p][k]:
                    return f"{c}|{p}|{k}"
    return None


def advantage(rec: Any) -> Any:
    """Planner minus the selected baseline, per seed."""
    t = rec["test"]
    return np.array(t["proposed"]["net"]) - np.array(t[rec["best_baseline"]]["net"])


def h_r2(out: Any, tight: Any, contracts: Any) -> Any:
    """The pre-registered rule, verbatim, over the 12 tight-setting-by-contract cells."""
    cells = {}
    for s in tight:
        for c in contracts:
            a_t, a_d = advantage(out[f"{s}|{c}"]), advantage(out[f"default|{c}"])
            cells[f"{s}|{c}"] = dict(paired(a_t, a_d), adv_tight=float(a_t.mean()), adv_default=float(a_d.mean()),
                                     bestbase_tight=out[f"{s}|{c}"]["best_baseline"], bestbase_default=out[f"default|{c}"]["best_baseline"])
    return dict(interval_rule(cells.values()), cells=cells)


def run(S: Study) -> dict:
    """The sweep (results_robot.json). The default cell must reproduce results_rq1_decomp.json exactly, or the study stops before the rule."""
    P = S.params; POLS = P["policies"]; settings = P["settings"]
    out = {"_meta": dict(label="EXTENSION", settings=settings, factors=P["factors"], tight=P["tight"], workers=S.protocol.workers, train_seeds=S.protocol.train,
                         test_seeds=S.protocol.test, policies=POLS, baselines=S.protocol.baselines)}
    t0 = time.time()
    with S.runner_pool() as rn:
        for s in settings:
            for c in rn.contracts:
                out[f"{s}|{c}"] = cell(rn, s, settings[s], c, POLS)
    bad = check_default(out, S.stored("results_rq1_decomp.json")["rq1"], S.protocol.contracts, POLS)
    out["_default_check"] = dict(exact_match=bad is None, first_mismatch=bad, reference="results_rq1_decomp.json rq1")
    if bad:
        S.write(out)
        raise SystemExit(f"STOP: default cell differs from the R1 RQ1 rerun at {bad}")
    out["_verdict_H_R2"] = h_r2(out, P["tight"], S.protocol.contracts)
    out["_meta"]["runtime_s_last"] = time.time() - t0
    return out
