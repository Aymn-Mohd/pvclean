"""Phase R2 UNREGISTERED DIAGNOSTICS, run after the pre-registered sweep to check its surprises. Nothing here enters the H-R2 verdict or
results/results_robot.json. Writes results/r2_checks.json.

  baselines  stored data: planner minus each conventional baseline per cell, and the H-R2 tally with threshold held as the baseline
  decomp     stored data: value of cleaning, tight minus default, as d_revenue - d_clean_cost - d_mission_cost
  frozen     default-tuned parameters in every setting (no retuning): the pure capacity effect on the planner and on threshold
  use        planner mission logs at each cell's tuned parameters: rows per mission, share of missions that fill the night or battery,
             share of robot night time used
  low        retuned, capacities below the pre-registered range (battery 1-4, availability 0.5 and 0.25): does the value of cleaning respond?
  retune     the H-R2 tally with tuning repeated on other train seeds, to size the tuning noise in the cell differences"""
from __future__ import annotations
from typing import Any
from pvclean import model
from pvclean.stats import paired
from .robot_sweep import advantage, cell
from .runner import inputs, over_key
import time
import numpy as np
from .study import Study

def use_job(a: Any) -> Any:
    """Worker: how full the planner's missions are on one seed."""
    par, c, s, over = a
    cfg = dict(model.CONFIG, **over, mission_log=True)
    clim, vexp, pbar = inputs(c, over_key(over), dict(model.CONFIG, **over))
    m = model.simulate("proposed", par, c, s, cfg=cfg, clim=clim, vexp=vexp, pbar=pbar)["missions"]
    full = [len(x["rows"]) == cfg.get("battery_rows") or x["end_min"] + cfg["service_min"] > cfg["night_min"] for x in m]
    return dict(n=len(m), rows=sum(len(x["rows"]) for x in m), full=sum(full), busy=sum(x["end_min"] for x in m) / (365 * cfg["night_min"]))


def tally(res: Any, tight: Any, contracts: Any) -> Any:
    """H-R2 counts for a dict of cells keyed like results_robot.json."""
    v = [paired(advantage(res[f"{s}|{c}"]), advantage(res[f"default|{c}"])) for s in tight for c in contracts]
    return dict(ci_wholly_above=sum(x["lo"] > 0 for x in v), ci_wholly_below=sum(x["hi"] < 0 for x in v),
                mean_nonpos=sum(x["mean"] <= 0 for x in v), means=[x["mean"] for x in v])


def run(S: Study) -> dict:
    """The R2 diagnostics (r2_checks.json)."""
    D = S.stored("results_robot.json"); P = S.params; TIGHT = P["tight"]; POLS = P["policies"]; SETTINGS = dict(P["settings"]); CON = S.protocol.contracts
    keys = [k for k in D if "|" in k]
    out = dict(_label="UNREGISTERED DIAGNOSTIC")
    t0 = time.time()
    out["baselines"] = {k: {b: paired(D[k]["test"]["proposed"]["net"], D[k]["test"][b]["net"]) for b in S.protocol.baselines} for k in keys}
    th = {k: dict(D[k], best_baseline="threshold") for k in keys}
    out["tally_threshold_held"] = tally(th, TIGHT, CON)
    out["tally_threshold_held"]["cells"] = {f"{s}|{c}": paired(advantage(th[f"{s}|{c}"]), advantage(th[f"default|{c}"]))
                                            for s in TIGHT for c in CON}
    out["decomp"] = {}
    for k in keys:
        s, c = k.split("|")
        a, b = D[k]["test"], D[f"default|{c}"]["test"]
        dd = lambda f: float(np.mean(np.array(a["proposed"][f]) - a["none"][f] - (np.array(b["proposed"][f]) - b["none"][f])))
        out["decomp"][k] = dict(d_voc=dd("net"), d_revenue=dd("revenue"), d_clean=dd("cost_clean"), d_mission=dd("cost_mission"))
    with S.runner_pool() as rn:
        out["frozen"] = {}
        for k in keys:
            s, c = k.split("|")
            par = {p: D[f"default|{c}"]["tuned"][p]["params"] for p in POLS}
            t = rn.evaluate(c, par, SETTINGS[s], {}, ["threshold", "proposed"])
            out["frozen"][k] = dict(value_of_cleaning=paired(t["proposed"]["net"], t["none"]["net"]),
                                    threshold_value=paired(t["threshold"]["net"], t["none"]["net"]),
                                    planner_threshold=paired(t["proposed"]["net"], t["threshold"]["net"]),
                                    planner_missions=float(np.mean(t["proposed"]["n_missions"])), planner_rows=float(np.mean(t["proposed"]["n_clean"])))
        out["use"] = {}
        for k in keys:
            s, c = k.split("|")
            r = rn.map(use_job, [(D[k]["tuned"]["proposed"]["params"], c, x, SETTINGS[s]) for x in rn.test])
            tot = {f: sum(x[f] for x in r) for f in ("n", "rows", "full")}
            out["use"][k] = dict(rows_per_mission=tot["rows"] / tot["n"], share_full=tot["full"] / tot["n"], night_use_year=float(np.mean([x["busy"] for x in r])))
        LOW = P["low"]; SETTINGS.update(LOW)
        out["low"] = {}
        for s in LOW:
            for c in rn.contracts:
                r = cell(rn, s, SETTINGS[s], c, POLS)
                out["low"][f"{s}|{c}"] = dict(best_baseline=r["best_baseline"], rows_per_night=r["rows_per_night"], metrics=r["metrics"],
                                              voc_ratio=r["metrics"]["value_of_cleaning"]["mean"] / D[f"default|{c}"]["metrics"]["value_of_cleaning"]["mean"])
        out["retune"] = {}
        for name, seeds in P["retune"].items():
            rt = rn.with_(train=seeds)
            res = {f"{s}|{c}": cell(rt, s, SETTINGS[s], c, POLS) for s in ["default"] + TIGHT for c in CON}
            out["retune"][name] = dict(tally(res, TIGHT, CON), params={k: v["tuned"]["proposed"]["params"] for k, v in res.items()},
                                       best_baseline={k: v["best_baseline"] for k, v in res.items()},
                                       adv={k: float(advantage(v).mean()) for k, v in res.items()})
    out["runtime_s"] = time.time() - t0
    return out
