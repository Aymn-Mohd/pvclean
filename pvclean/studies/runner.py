"""Tuning and evaluation: runs policy jobs on a worker pool under an explicit Protocol. Jobs are seeded and pool.map keeps job order, so results do not depend on worker count."""
from __future__ import annotations
import json
from multiprocessing import Pool
from typing import Any, Callable, Iterable, Sequence
import numpy as np
from pvclean import model
from pvclean.config import Protocol
from pvclean.stats import ci95

KEEP = ("net", "revenue", "energy_kwh", "n_clean", "n_missions", "cost_clean", "cost_mission", "cost_insp")
_INPUTS: dict[tuple, tuple] = {}


def inputs(contract: str, cfg_key: Any, cfg: dict[str, Any]) -> tuple:
    """Planner inputs, cached per process."""
    k = (contract, cfg_key)
    if k not in _INPUTS:
        _INPUTS[k] = model.planner_inputs(contract, cfg)
    return _INPUTS[k]


def over_key(over: dict[str, Any]) -> tuple:
    """Cache key of a parameter override."""
    return tuple(sorted((k, str(v)) for k, v in over.items()))


def job(args: tuple) -> tuple[tuple, dict[str, Any]]:
    """args = (policy, params, contract, seed, info, sigma, hetero, overrides). Overrides may hold `_inp`: planner inputs built from other (training) years."""
    pol, par, contract, seed, info, sigma, hetero, cfg_over = args
    cfg_over = dict(cfg_over)
    inp_over = cfg_over.pop("_inp", None)
    cfg = model.merged(cfg_over)
    icfg = dict(cfg); icfg.update(inp_over or {})
    clim, vexp, pbar = inputs(contract, over_key({**cfg_over, **(inp_over or {})}), icfg)
    r = model.simulate(pol, par, contract, seed, info=info, sigma=sigma, cfg=cfg, hetero=hetero, clim=clim, vexp=vexp, pbar=pbar)
    r.pop("trace", None)
    return args, r


def record_job(args: tuple) -> Any:
    """A job reduced to the KEEP fields, or ('vref', contract, seed, overrides): the production-weighted mean contract value of the seed-year."""
    if args[0] == "vref":
        _, contract, seed, over = args
        cfg = model.merged(over)
        pdc = model.weather(seed, cfg)["pdc"]; val = model.contract_value(contract, seed, cfg)[0]
        return float((pdc * val).sum() / pdc.sum())
    a, r = job(args)
    return {k: float(r[k]) for k in KEEP}


class Runner:
    """A Protocol and a worker pool. `with_()` gives a runner on the same pool with other seeds or grids."""

    def __init__(self, protocol: Protocol, pool: Any = None) -> None:
        self.protocol = protocol
        self.pool = pool
        self._owns_pool = pool is None

    def __enter__(self) -> "Runner":
        if self.pool is None:
            self.pool = Pool(self.protocol.workers)
        return self

    def __exit__(self, *exc: Any) -> None:
        if self._owns_pool and self.pool is not None:
            self.pool.close(); self.pool.join(); self.pool = None

    train = property(lambda self: self.protocol.train)
    test = property(lambda self: self.protocol.test)
    grids = property(lambda self: self.protocol.grids)
    contracts = property(lambda self: self.protocol.contracts)
    baselines = property(lambda self: self.protocol.baselines)

    def with_(self, **kw: Any) -> "Runner":
        """A runner on the same pool with some protocol fields replaced."""
        return Runner(self.protocol.with_(**kw), self.pool)

    def map(self, fn: Callable, items: Iterable, chunksize: int | None = None) -> list:
        """pool.map; keeps job order."""
        return self.pool.map(fn, items, chunksize=chunksize)

    def imap_unordered(self, fn: Callable, items: Iterable, chunksize: int = 1) -> Any:
        """pool.imap_unordered; results come in completion order."""
        return self.pool.imap_unordered(fn, items, chunksize=chunksize)

    def _best(self, jobs: list[tuple], nets: Sequence[float], policies: Sequence[str]) -> dict[str, dict[str, Any]]:
        """Best parameters per policy by training mean net; ties go to the first in grid order."""
        score: dict[tuple, list[float]] = {}
        for (p, par, *_), r in zip(jobs, nets):
            score.setdefault((p, json.dumps(par, sort_keys=True)), []).append(r)
        best = {}
        for p in policies:
            m, k = max(((float(np.mean(v)), k) for k, v in score.items() if k[0] == p), key=lambda c: c[0])
            best[p] = dict(params=json.loads(k[1]), train_mean=m)
        return best

    def tune(self, contract: str, over: dict[str, Any], policies: Sequence[str], info: str = "site", hetero: float = 1.0) -> dict[str, dict[str, Any]]:
        """Best parameters and training mean per policy."""
        jobs = [(p, par, contract, s, info, 0.01, hetero, over) for p in policies for par in self.grids[p] for s in self.train]
        return self._best(jobs, [r["net"] for r in self.map(record_job, jobs, chunksize=8)], policies)

    def tune_params(self, contract: str, cfg_over: dict[str, Any] | None = None, policies: Sequence[str] | None = None, info: str = "site", hetero: float = 1.0) -> dict[str, dict[str, Any]]:
        """Best parameters per policy, without the training mean."""
        pols = policies or list(self.grids)
        return {p: v["params"] for p, v in self.tune(contract, cfg_over or {}, pols, info, hetero).items()}

    def evaluate(self, contract: str, params: dict[str, dict[str, Any]], over_te: dict[str, Any], over_tr: dict[str, Any], policies: Sequence[str]) -> dict[str, Any]:
        """Per-seed records on the test seeds; planner inputs from the training years (over_tr)."""
        over = dict(over_te); over["_inp"] = dict(over_tr)
        jobs = [("none", {}, contract, s, "site", 0.01, 1.0, over) for s in self.test]
        jobs += [(p, params[p], contract, s, "site", 0.01, 1.0, over) for p in policies for s in self.test]
        res = self.map(record_job, jobs, chunksize=8)
        n = len(self.test)
        none = res[:n]
        out: dict[str, Any] = {"none": {k: [r[k] for r in none] for k in KEEP}}
        for i, p in enumerate(policies):
            rr = res[n * (i + 1):n * (i + 2)]
            out[p] = {k: [r[k] for r in rr] for k in KEEP}
            out[p]["inc_net"] = [r["net"] - z["net"] for r, z in zip(rr, none)]
            out[p]["params"] = params[p]
        return out

    def evaluate_summary(self, contract: str, best: dict[str, dict[str, Any]], cfg_over: dict[str, Any] | None = None, info: str = "site", sigma: float = 0.01, hetero: float = 1.0,
                         policies: Sequence[str] | None = None) -> dict[str, Any]:
        """Intervals per policy over the test seeds, against no cleaning."""
        cfg_over = cfg_over or {}
        policies = policies or list(best)
        jobs = [("none", {}, contract, s, info, sigma, hetero, cfg_over) for s in self.test]
        jobs += [(p, best[p], contract, s, info, sigma, hetero, cfg_over) for p in policies for s in self.test]
        res = self.map(job, jobs, chunksize=8)
        base = {a[3]: r for a, r in res if a[0] == "none"}
        out = {}
        for p in policies:
            rows = [(a[3], r) for a, r in res if a[0] == p]
            inc = [r["net"] - base[s]["net"] for s, r in rows]
            out[p] = dict(params=best[p], inc_net=ci95(inc), inc_net_seeds=inc,
                          energy_rec_mwh=ci95([(r["energy_kwh"] - base[s]["energy_kwh"]) / 1000 for s, r in rows]),
                          n_clean=ci95([r["n_clean"] for s, r in rows]), n_missions=ci95([r["n_missions"] for s, r in rows]),
                          maint_cost=ci95([r["cost_clean"] + r["cost_mission"] + r["cost_insp"] for s, r in rows]),
                          insp_cost=ci95([r["cost_insp"] for s, r in rows]), revenue_none=ci95([base[s]["revenue"] for s, r in rows]),
                          energy_none_mwh=ci95([base[s]["energy_kwh"] / 1000 for s, r in rows]))
        return out

    def evaluate_real(self, contract: str, best: dict[str, dict[str, Any]], over_te: dict[str, Any], over_tr: dict[str, Any], policies: Sequence[str]) -> dict[str, Any]:
        """evaluate_summary with planner inputs from the training years."""
        over = dict(over_te); over["_inp"] = dict(over_tr)
        return self.evaluate_summary(contract, best, cfg_over=over, policies=policies)
