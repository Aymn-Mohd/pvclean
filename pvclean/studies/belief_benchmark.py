"""EXP-05: optimisation quality with everything but the decision rule held fixed.
Part A (in-model, deterministic): the truth equals the planner's belief (expected dust increment, no rain, equal row exposure,
climatological production, expected prices), the state is known, the objective/constraints/action set/timestamp are identical.
Compared: full-horizon certified MILP (J*), receding-horizon MILP with horizon H and terminal tail, and heuristics tuned IN the
same world (which favours the heuristics). Any shortfall of a MILP arm below J* is therefore a horizon/terminal-value or solver effect.
Part B (stochastic small instances): forecast-matched threshold baseline ('ft') tuned on training seeds, evaluated on seeds 0-19.
Writes part_a and part_b of results_matched.json."""
from __future__ import annotations
from typing import Any
import time
from pvclean import model
from pvclean.exact import belief_world, make_mpc, row_tables, schedule_value, solve
from .study import Study

def part_a(args: Any) -> Any:
    """One setting and window of part A: the MILP arms and tuned heuristics in the belief world."""
    contract, crow, d0, instance, arms, grids, heur = args
    cfg = dict(model.CONFIG); cfg.update(instance, c_row=crow, d0=d0, d1=d0 + 60)
    c, v, p = model.planner_inputs(contract, cfg)
    w = belief_world(c, v)
    Rev = row_tables(0, contract, cfg, world=w)
    t0 = time.time(); res, sched = solve(Rev, cfg, 120); rt = time.time() - t0
    none = schedule_value(Rev, [], cfg)
    out = dict(contract=contract, crow=crow, d0=d0, jstar=schedule_value(Rev, sched, cfg) - none,
               jstar_status=int(res.status), jstar_gap=None if res.mip_gap is None else float(res.mip_gap), jstar_runtime=rt,
               jstar_viol=model.schedule_violations(sched, cfg), mpc={}, heur={})
    base = model.simulate("none", {}, contract, 0, info="perfect", cfg=cfg, world=w)["net"]
    for name, kw in arms.items():
        lg = []; t0 = time.time()
        r = model.simulate("mpc", {"fn": make_mpc(log=lg, **kw)}, contract, 0, info="perfect",
                         cfg=cfg, clim=c, vexp=v, pbar=p, world=w)
        out["mpc"][name] = dict(gain=r["net"] - base, n_clean=r["n_clean"], n_missions=r["n_missions"], runtime=time.time() - t0,
                                max_gap=max([x["mip_gap"] or 0.0 for x in lg] or [0.0]), statuses=sorted({x["status"] for x in lg}),
                                first_obj=lg[0]["obj"] if lg else None, viol=model.schedule_violations(r["sched"], cfg))
    for pol in heur:
        best = None
        for par in grids[pol]:
            r = model.simulate(pol, par, contract, 0, info="perfect", cfg=cfg, clim=c, vexp=v, pbar=p, world=w)
            if best is None or r["net"] > best[0]:
                best = (r["net"], par, r["n_clean"])
        out["heur"][pol] = dict(gain=best[0] - base, params=best[1], n_clean=best[2])
    return out


def run(S: Study) -> dict:
    """Parts A and B (keys part_a and part_b of results_matched.json). Part A collects in completion order, as the original did, so its list order can differ between runs."""
    P = S.params; settings = [tuple(x) for x in P["settings"]]; out = {}
    tasks = [(c, cr, d0, P["instance_a"], P["mpc_arms"], {p: S.protocol.grids[p] for p in P["heuristics"]}, P["heuristics"]) for (c, cr) in settings for d0 in P["windows"]]
    tasks.sort(key=lambda t: -t[2] % 7)
    with S.runner_pool() as rn:
        out["part_a"] = list(rn.imap_unordered(part_a, tasks, chunksize=1))
        rb = rn.with_(test=list(range(*P["part_b_test_seeds"]))); res = {}
        for contract, crow in settings:
            over = dict(P["instance_b"], c_row=crow); pols = P["part_b_policies"]
            best = rb.tune_params(contract, cfg_over=over, policies=pols)
            ev = rb.evaluate_summary(contract, best, cfg_over=over, policies=pols)
            res[f"{contract}|c{crow}"] = {p: dict(params=ev[p]["params"], seeds=ev[p]["inc_net_seeds"], inc=ev[p]["inc_net"]) for p in pols}
        out["part_b"] = res
    return out
