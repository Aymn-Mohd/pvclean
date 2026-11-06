"""Exact benchmarks on small instances: the clairvoyant optimum against tuned heuristics, the information-matched open-loop optimum, and the 14-day receding-horizon MILP."""
from __future__ import annotations
from typing import Any
from pvclean import model
from pvclean.exact import make_mpc, row_tables, schedule_value, solve
from .study import Study

_IN: dict[tuple, tuple] = {}


def clairvoyant(args: tuple) -> dict[str, Any]:
    """Worker: the clairvoyant optimum of one instance."""
    seed, contract, over, limit = args
    cfg = model.merged(over)
    Rev = row_tables(seed, contract, cfg)
    res, sched = solve(Rev, cfg, limit)
    none = schedule_value(Rev, [], cfg)
    return dict(seed=seed, opt=schedule_value(Rev, sched, cfg) - none, gap=res.mip_gap if res.mip_gap is not None else float("nan"), status=int(res.status), none=none)


def belief_plan(args: tuple) -> dict[str, Any]:
    """Worker: plans on the belief and scores on the true instance."""
    seed, contract, over, limit = args
    cfg = model.merged(over)
    key = (contract, tuple(sorted(over.items())))
    if key not in _IN:
        c, v, p = model.planner_inputs(contract, cfg); _IN[key] = (c, v)
    Rev = row_tables(seed, contract, cfg)
    Rb = row_tables(seed, contract, cfg, belief=_IN[key])
    none = schedule_value(Rev, [], cfg)
    res, sched = solve(Rb, cfg, limit)
    return dict(seed=seed, matched=schedule_value(Rev, sched, cfg) - none, gap=res.mip_gap if res.mip_gap is not None else float("nan"))


def receding(args: tuple) -> dict[str, Any]:
    """Worker: the receding-horizon MILP on one instance."""
    seed, contract, over, horizon = args
    cfg = model.merged(over)
    c, v, p = model.planner_inputs(contract, cfg)
    base = model.simulate("none", {}, contract, seed, cfg=cfg)["net"]
    r = model.simulate("mpc", {"fn": make_mpc(horizon=horizon)}, contract, seed, cfg=cfg, clim=c, vexp=v, pbar=p)
    return dict(seed=seed, mpc=r["net"] - base, n_clean=r["n_clean"])


def exact(S: Study) -> dict[str, Any]:
    """Clairvoyant optimum against tuned heuristics (results_exact.json)."""
    P = S.params; out = {}; pols = P["policies"]
    with S.runner_pool() as rn:
        for contract in P["contracts"]:
            for crow in P["crow"]:
                over = dict(P["instance"], c_row=crow)
                res: dict[str, Any] = {"exact": rn.map(clairvoyant, [(s, contract, over, P["time_limit"]) for s in rn.test])}
                for tag, extra, info in (("site", {}, "site"), ("matched", {"fc_mode": "perfect"}, "perfect")):
                    o = dict(over, **extra)
                    best = rn.tune_params(contract, cfg_over=o, policies=pols, info=info)
                    ev = rn.evaluate_summary(contract, best, cfg_over=o, info=info, policies=pols)
                    res[tag] = {p: dict(inc=ev[p]["inc_net"], seeds=ev[p]["inc_net_seeds"], params=ev[p]["params"]) for p in pols}
                out[f"{contract}|c{crow}"] = res
    return out


def exact_matched(S: Study) -> dict[str, Any]:
    """The optimiser plans open-loop on the planner's belief and the schedule is scored on the true instance (results_exact_matched.json)."""
    P = S.params; out = {}
    with S.runner_pool() as rn:
        for contract in P["contracts"]:
            for crow in P["crow"]:
                out[f"{contract}|c{crow}"] = rn.map(belief_plan, [(s, contract, dict(P["instance"], c_row=crow), P["time_limit"]) for s in rn.test])
    return out


def mpc(S: Study) -> dict[str, Any]:
    """Receding-horizon MILP with the station-information planner's information (results_mpc.json)."""
    P = S.params; out = {}
    with S.runner_pool() as rn:
        for contract in P["contracts"]:
            for crow in P["crow"]:
                out[f"{contract}|c{crow}"] = rn.map(receding, [(s, contract, dict(P["instance"], c_row=crow), P["horizon"]) for s in rn.test])
    return out
