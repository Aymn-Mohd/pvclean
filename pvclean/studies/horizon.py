"""EXP-03/04/05: horizon sensitivity, terminal value and information ladder for the receding-horizon exact optimiser,
on the v9 small instances (6 rows, days 120-180, seeds 0-19, truth = full stochastic simulator).
Writes results_horizon.json."""
from __future__ import annotations
from pvclean import model
from pvclean.exact import make_mpc
from typing import Any
import time
from .study import Study

def one(args: Any) -> Any:
    """Worker: one arm on one instance."""
    contract, crow, arm, seed, kw, info, instance, limit, gap = args
    cfg = dict(model.CONFIG); cfg.update(instance, c_row=crow)
    c, v, p = model.planner_inputs(contract, cfg)
    base = model.simulate("none", {}, contract, seed, cfg=cfg)["net"]
    lg = []
    t0 = time.time()
    r = model.simulate("mpc", {"fn": make_mpc(log=lg, time_limit=limit, gap=gap, **kw)}, contract, seed, info=info,
                     cfg=cfg, clim=c, vexp=v, pbar=p, record=True)
    st = {}
    for x in lg: st[x["status"]] = st.get(x["status"], 0) + 1
    gaps = [x["mip_gap"] for x in lg if x["mip_gap"] is not None]
    return dict(contract=contract, crow=crow, arm=arm, seed=seed, gain=r["net"] - base, n_clean=r["n_clean"], n_missions=r["n_missions"],
                runtime=time.time() - t0, n_solves=len(lg), max_solve_s=max(x["runtime"] for x in lg) if lg else 0.0,
                status_counts=st, max_gap=max(gaps) if gaps else None, no_solution=sum(1 for x in lg if not x["has_solution"]),
                first_obj=lg[0]["obj"] if lg else None, first_bound=lg[0]["bound"] if lg else None,
                viol=model.schedule_violations(r["sched"], cfg), final_sr_mean=float(r["trace"][-1].mean()), final_sr_min=float(r["trace"][-1].min()))


def run(S: Study) -> Any:
    """All arms in all settings (results_horizon.json), longest first for load balance."""
    P = S.params; arms = P["arms"]
    tasks = [(c, cr, a, s, arms[a]["mpc"], arms[a]["info"], P["instance"], P["time_limit"], P["gap"]) for c, cr, plan in P["plan"] for a in plan for s in S.protocol.test]
    tasks.sort(key=lambda t: -P["load"].get(t[2], 10))
    done = []
    with S.runner_pool() as rn:
        for res in rn.imap_unordered(one, tasks, chunksize=1):
            done.append(res)
    return done
