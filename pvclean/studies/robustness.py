"""Phase R1b stage 3 (SENSITIVITY, pre-registered in docs/EXPERIMENT_LOG.md "Phase R1b"): robustness of the generated-market RQ1.

Variants (each retuned on the train seeds with the RQ1 grids, tested on the same 50 test seeds, four contracts):
  a_noaccess     no crop-access windows (blackouts = ())
  b_bias+25      station measures 1.25 x the site soiling increment (cfg station_bias = +0.25)
  b_bias-25      station measures 0.75 x the site soiling increment (station_bias = -0.25)
  c_eff098       robot cleaning leaves SR = 0.98 instead of 0.995 (clean_residual = 0.02)
  d_continuous   three consecutive simulated years per seed with the state carried over and no clean reset (simulate
                 init/carry); planning horizons wrap into the next year's climatology (wrap_horizon). Year k of chain s uses
                 seed s + 10000 k (k = 0, 1, 2), so year 1 of a test chain is the default test seed. Score = mean annual net of
                 years 2 and 3; tuning uses the same score on the train chains.
Default = the RQ1 rerun with per-seed storage in results/results_rq1_decomp.json (rq1), same policies and tuning.
Comparisons per contract: planner minus the training-selected best baseline (primary) and planner minus FT.
Rule (pre-registered): ROBUST if the sign of the paired mean matches the default and, where the default interval excludes 0,
the variant's interval does not lie wholly on the other side of 0; otherwise NOT ROBUST.
Writes results_robust.json."""
from __future__ import annotations
from typing import Any
from pvclean import model
from pvclean.stats import paired, robust_rule
from .runner import KEEP, inputs, over_key
import json, time
import numpy as np
from .study import Study

def chain_job(args: Any) -> Any:
    """Three-year continuous chain for seed s; returns the mean of years 2 and 3 of each kept field."""
    pol, par, contract, s, over, chain = args
    cfg = dict(model.CONFIG); cfg.update(over)
    clim, vexp, pbar = inputs(contract, over_key(over), cfg)
    st = None; yrs = []
    for off in chain:
        r = model.simulate(pol, par, contract, s + off, cfg=cfg, clim=clim, vexp=vexp, pbar=pbar, init=st)
        st = r["state"]; yrs.append(r)
    return {k: float(np.mean([y[k] for y in yrs[1:]])) for k in KEEP}


def tune_chain(rn: Any, c: Any, over: Any, POLS: Any, chain: Any) -> Any:
    """Tunes on three-year chains."""
    jobs = [(p, par, c, s, over, chain) for p in POLS for par in rn.grids[p] for s in rn.train]
    res = rn.map(chain_job, jobs, chunksize=4)
    score = {}
    for (p, par, *_), r in zip(jobs, res):
        score.setdefault((p, json.dumps(par, sort_keys=True)), []).append(r["net"])
    best = {}
    for p in POLS:
        m, k = max(((float(np.mean(v)), k) for k, v in score.items() if k[0] == p), key=lambda c_: c_[0])
        best[p] = dict(params=json.loads(k[1]), train_mean=m)
    return best


def eval_chain(rn: Any, c: Any, params: Any, over: Any, POLS: Any, chain: Any) -> Any:
    """Tests on three-year chains."""
    jobs = [("none", {}, c, s, over, chain) for s in rn.test] + [(p, params[p], c, s, over, chain) for p in POLS for s in rn.test]
    res = rn.map(chain_job, jobs, chunksize=4)
    n = len(rn.test); none = res[:n]
    out = {"none": {k: [r[k] for r in none] for k in KEEP}}
    for i, p in enumerate(POLS):
        rr = res[n * (i + 1):n * (i + 2)]
        out[p] = {k: [r[k] for r in rr] for k in KEEP}
        out[p]["inc_net"] = [r["net"] - z["net"] for r, z in zip(rr, none)]
        out[p]["params"] = params[p]
    return out


def compare(tuned: Any, test: Any, BASE: Any) -> Any:
    """The selected baseline and the two paired comparisons."""
    bb = max(BASE, key=lambda p: tuned[p]["train_mean"])
    return bb, {"planner-bestbase": paired(test["proposed"]["net"], test[bb]["net"]),
                "planner-ft": paired(test["proposed"]["net"], test["ft"]["net"])}


def run(S: Study) -> dict:
    """The variants (results_robust.json)."""
    P = S.params; POLS = P["policies"]; variants = P["variants"]; chain = tuple(P["chain_seed_offsets"]); BASE = S.protocol.baselines
    D = S.stored("results_rq1_decomp.json")["rq1"]
    out = {"_default": {}}
    for c in S.protocol.contracts:
        bb, cmp_ = compare(D[c]["tuned"], D[c]["test"], BASE)
        out["_default"][c] = dict(best_baseline=bb, cmp=cmp_, source="results_rq1_decomp.json rq1")
    out["_meta"] = dict(label="SENSITIVITY", variants=variants, chain_seed_offsets=chain, workers=S.protocol.workers, train_seeds=S.protocol.train, test_seeds=S.protocol.test, policies=POLS)
    t0 = time.time()
    with S.runner_pool() as rn:
        for v, over in variants.items():
            over = {k: tuple(x) if isinstance(x, list) else x for k, x in over.items()}
            for c in rn.contracts:
                if v == "d_continuous":
                    best = tune_chain(rn, c, over, POLS, chain)
                    test = eval_chain(rn, c, {p: best[p]["params"] for p in POLS}, over, POLS, chain)
                else:
                    best = rn.tune(c, over, POLS)
                    test = rn.evaluate(c, {p: best[p]["params"] for p in POLS}, over, {}, POLS)
                bb, cmp_ = compare(best, test, BASE)
                dflt = out["_default"][c]["cmp"]
                out[f"{v}|{c}"] = dict(variant=v, contract=c, over=over, tuned=best, test=test, best_baseline=bb, cmp=cmp_, verdict={k: robust_rule(dflt[k], cmp_[k]) for k in cmp_})
    out["_meta"]["runtime_s_last"] = time.time() - t0
    return out
