"""Phase R7: SENSITIVITY runs requested by reviewers, over the 56 matched-site case-years. No decision rules. Definitions: docs/records/decisions.md, "Phase R7 (sensitivity,
specified before the runs)". Every variant retunes every policy on the training years only (chrono.run_fold)."""
from __future__ import annotations
import json
import os
import time
from typing import Any
import numpy as np
from pvclean import model
from pvclean.core.robot import schedule_violations
from pvclean.core.soiling import rain_forecast
from pvclean.exact import path_values, solve_oracle, sr_tables
from pvclean.forecasts import fc_value
from pvclean.stats import paired
from .chrono import run_fold
from .matched import fold_test_year
from .r4 import market_of, site_over
from .r6 import ALL_SITES, cases, overs
from .study import Study

POLS = ("threshold", "ft", "proposed")
SOIL = 0.0030
# name -> (fc_mode, extra config); F4 is an information upper bound, not deployable.
FORECASTS = {"F2": ("roll", {}), "F7d": ("roll", dict(roll_days=7)), "F56d": ("roll", dict(roll_days=56)), "FHW": ("roll_hw", {}), "F3": ("dayahead", {}), "F4": ("perfect", {})}


def sites_of(S: Study) -> tuple[str, ...]:
    return tuple(S.params.get("sites", ALL_SITES))


def compact(rec: dict[str, Any]) -> dict[str, Any]:
    """Per-seed nets of no cleaning and the three policies, their tuned parameters, and the two paired differences."""
    t = rec["test"]["F2"]
    out = dict(none=list(t["none"]["net"]), net={p: list(t[p]["net"]) for p in POLS}, n_clean={p: float(np.mean(t[p]["n_clean"])) for p in POLS},
               params={p: rec["tuned"]["F2"][p]["params"] for p in POLS}, train_mean={p: rec["tuned"]["F2"][p]["train_mean"] for p in POLS})
    out["planner_ft"] = paired(t["proposed"]["net"], t["ft"]["net"]); out["ft_plain"] = paired(t["ft"]["net"], t["threshold"]["net"])
    out["value"] = {p: float(np.mean(np.subtract(t[p]["net"], t["none"]["net"]))) for p in POLS}
    return out


def variant(rn: Any, site: str, c: str, fold: str, fc_mode: str = "roll", extra: dict[str, Any] | None = None, soil: float = SOIL) -> dict[str, Any]:
    """One case-year under one variant, every policy retuned on the training years."""
    rec = run_fold(rn, market_of(site), c, fold, extra=dict(site_over(site, fold_test_year(fold), soil), **(extra or {})), modes={"F2": fc_mode})
    return compact(rec)


def arms_job(S: Study, arms: dict[str, dict[str, Any]], label: str = "SENSITIVITY") -> dict[str, Any]:
    """Every case-year under every arm. An arm is dict(fc_mode=..., extra=..., soil=...)."""
    t0 = time.time(); sites = sites_of(S); out: dict[str, Any] = {}
    with S.runner_pool() as rn:
        for name, a in arms.items():
            out[name] = dict(spec={k: v for k, v in a.items()}, rows={f"{s}|{c}|{f}": variant(rn, s, c, f, a.get("fc_mode", "roll"), a.get("extra"), a.get("soil", SOIL)) for s, c, f in cases(sites)})
            print(name, f"{time.time() - t0:.0f}s", flush=True)
    return dict(_meta=dict(label=label, train_seeds=S.protocol.train, test_seeds=S.protocol.test, grids=S.protocol.grids, workers=S.protocol.workers, runtime_s_last=time.time() - t0), arms=out)


def forecast_job(S: Study) -> dict[str, Any]:
    """Price forecasts F2, F7d, F56d, FHW, F3 and F4 (results_r7_forecast.json)."""
    return arms_job(S, {n: dict(fc_mode=m, extra=x) for n, (m, x) in FORECASTS.items() if n in S.params.get("forecasts", FORECASTS)})


def abstain_job(S: Study) -> dict[str, Any]:
    """The planner may choose no missions at all (kappa = inf) in its grid (results_r7_abstain.json)."""
    return arms_job(S, {"abstain": {}})


def dust_job(S: Study) -> dict[str, Any]:
    """Mean dust rate (results_r7_dust.json)."""
    return arms_job(S, {f"soil{s * 100:.2f}": dict(soil=s) for s in S.params["soil_mean"]})


def rain_job(S: Study) -> dict[str, Any]:
    """Rain-cleaning effectiveness, one setting at a time (results_r7_rain.json)."""
    return arms_job(S, {f"{k}={v}": dict(extra={k: v}) for k, vs in S.params["rain"].items() for v in vs})


def cost_job(S: Study) -> dict[str, Any]:
    """c_row and c_mission scaled together (results_r7_cost.json)."""
    c = model.CONFIG
    return arms_job(S, {f"x{m}": dict(extra=dict(c_row=c["c_row"] * m, c_mission=c["c_mission"] * m)) for m in S.params["multipliers"]})


def belief_G(kind: str, seed: int, c: str, cfg: dict[str, Any]) -> np.ndarray:
    """Path tables an information-restricted planner plans on. A: true prices, rain known only through the policies' rain forecast flags (a flagged day gets rain_full_mm,
    no other rain). B: prices replaced by the F2 forecast issued at the start of each day, true rain. D: true prices and rain, each row soils as the station estimate
    assumes. full: the truth."""
    if kind == "full":
        return path_values(seed, c, cfg)
    if kind == "A":
        rain = model.weather(seed, cfg)["rain"]
        flags = rain_forecast(rain, seed, cfg)
        return path_values(seed, c, cfg, SR=sr_tables(seed, cfg, rain=np.where(flags, cfg["rain_full_mm"], 0.0)))
    if kind == "B":
        val, warm = model.contract_value(c, seed, cfg)
        assert warm is not None, "F2 needs the warm-up"
        vhat = np.concatenate([fc_value("roll", d, np.arange(24 * d, 24 * d + 24), val, np.zeros_like(val), 1, warm, roll_days=cfg["roll_days"]) for d in range(365)])
        return path_values(seed, c, cfg, val=vhat)
    if kind == "D":
        return path_values(seed, c, cfg, SR=sr_tables(seed, cfg, station=True))
    raise ValueError(kind)


def split_unit(args: tuple) -> dict[str, Any]:
    """Worker: plan on the belief tables of one kind, then score the schedule in the simulator (the truth). args = (site, contract, fold, seed, kind)."""
    site, c, f, seed, kind = args
    t0 = time.time(); cfg = model.merged(overs(site, f)[0]); d0 = cfg.get("d0", 0)
    r = solve_oracle(belief_G(kind, seed, c, cfg), cfg)
    sched = [(d0 + t, rows) for t, rows in r["sched"]]
    none = model.simulate("none", {}, c, seed, cfg=cfg)["net"]
    rep = model.simulate("replay", dict(sched=dict(sched)), c, seed, cfg=cfg)
    return dict(key=f"{site}|{c}|{f}", seed=seed, kind=kind, none=none, value=rep["net"] - none, plan_value=r["value"] - none, n_clean=rep["n_clean"], n_missions=rep["n_missions"],
                violations=schedule_violations(sched, cfg), runtime=time.time() - t0, sched=sched)


def qualifying(S: Study) -> list[str]:
    """Case-years whose R6 oracle value (mean over its seeds) is at least the H-R6a cut."""
    from pvclean.stats import HEADROOM_CUT
    O = S.stored("results_r6_oracle.json")["rows"]
    return [k for k in map("|".join, cases(sites_of(S))) if float(np.mean(O[k]["value"])) >= HEADROOM_CUT]


def oracle_split_job(S: Study) -> dict[str, Any]:
    """Oracles A, B and D on the qualifying case-years and the first seeds; C is the stored R6 oracle on the same seeds (results_r7_oracle_split.json). Units are saved as they
    finish, so a stopped run resumes."""
    t0 = time.time(); seeds = list(S.params["seeds"]); kinds = list(S.params["kinds"]); keys = S.params.get("keys") or qualifying(S)
    part = S.out_path(S.output + ".partial.jsonl"); done: dict[tuple, dict[str, Any]] = {}
    if os.path.exists(part):
        for line in open(part):
            r = json.loads(line); done[(r["key"], r["seed"], r["kind"])] = r
    todo = [(*k.split("|"), x, kd) for kd in kinds for k in keys for x in seeds if (k, x, kd) not in done]
    with S.runner_pool() as rn:
        with open(part, "a") as out:
            for r in rn.imap_unordered(split_unit, todo, chunksize=1):
                done[(r["key"], r["seed"], r["kind"])] = r
                out.write(json.dumps(r, default=float) + "\n"); out.flush()
    O = S.stored("results_r6_oracle.json")["rows"]; rows: dict[str, Any] = {}
    for k in keys:
        o = O[k]; idx = [o["seeds"].index(x) for x in seeds]
        rows[k] = dict(C=dict(value=[o["value"][i] for i in idx], none=[o["none"][i] for i in idx], upper=[o["upper"][i] for i in idx]),
                       **{kd: {f: [done[(k, x, kd)][f] for x in seeds] for f in ("value", "plan_value", "none", "n_clean", "n_missions", "violations", "runtime", "sched")} for kd in kinds})
    meta = dict(label="SENSITIVITY", seeds=seeds, kinds=kinds, n_keys=len(keys), units=len(todo), workers=S.protocol.workers, runtime_s_last=time.time() - t0,
                note="C is results_r6_oracle.json on these seeds. A, B and D are open-loop full-year plans on restricted information, scored in the simulator.")
    os.remove(part)
    return dict(_meta=meta, rows=rows)
