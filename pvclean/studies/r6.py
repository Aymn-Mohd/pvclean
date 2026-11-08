"""Phase R6: headroom against perfect foresight, FT against the plain loss threshold, and tuning-inclusive intervals, over the 56 matched-site case-years. Pre-registration:
docs/records/decisions.md, "Phase R6"."""
from __future__ import annotations
import json
import os
import time
from typing import Any
import numpy as np
from pvclean import model
from pvclean.core.robot import schedule_violations
from pvclean.exact import path_values, solve_oracle
from pvclean.stats import paired
from .chrono import CONTRACTS, FOLDS
from .matched import FOLD_NAMES, MARKET_SITES, fold_test_year
from .r4 import F2_ONLY, NEW_SITES, R3_SITES, market_of, run_case, site_over
from .r5 import R5_SITES
from .runner import job
from .study import Study

ALL_SITES = R3_SITES + NEW_SITES + R5_SITES
POLICIES = ("fixed", "threshold", "econ", "ft", "proposed")


def sites_of(S: Study) -> tuple[str, ...]:
    """The sites of a study: params `sites`, by default all 14."""
    return tuple(S.params.get("sites", ALL_SITES))


def cases(sites: tuple[str, ...]) -> list[tuple[str, str, str]]:
    """Site x contract x fold."""
    return [(s, c, f) for s in sites for c in CONTRACTS for f in FOLD_NAMES]


def overs(site: str, fold: str) -> tuple[dict[str, Any], dict[str, Any]]:
    """Test and training overrides of a fold, as chrono.run_fold builds them."""
    ex = dict(real_value=market_of(site), fc_mode="roll", roll_min_hist=1, **site_over(site, fold_test_year(fold)))
    tr, te = FOLDS[fold]
    return dict(ex, real_years=te), dict(ex, real_years=tr)


def stored_records(S: Study) -> dict[str, Any]:
    """The stored full record of every case-year, by site|contract|fold."""
    out: dict[str, Any] = {}
    m = S.stored("results_matched.json")["r3"]
    for mk, s in MARKET_SITES.items():
        for c in CONTRACTS:
            for f in FOLD_NAMES:
                out[f"{s}|{c}|{f}"] = m[f"soil0.30|{mk}|{c}|{f}"]
    for k, v in S.stored("results_r4_sites.json")["r4"].items():
        out[k.split("|", 1)[1]] = v
    for c in CONTRACTS:
        for k, v in S.stored(f"results_r5_{c}.json")["r5"].items():
            out[k.split("|", 1)[1]] = v
    return out


def oracle_unit(args: tuple) -> dict[str, Any]:
    """Worker: the oracle of one site, contract, fold and seed. The schedule is replayed through the simulator, so its value comes from the simulator's ledger. args = (site, contract, fold, seed, start
    mission nights in absolute days, overrides[, incumbent]). An incumbent is a known feasible schedule [(day, rows)], a tuned policy's: it is replayed too, and kept if the search ends below it, since
    the oracle is at least every feasible schedule."""
    site, c, f, seed, starts, over = args[:6]; inc = args[6] if len(args) > 6 else None
    t0 = time.time(); te = dict(overs(site, f)[0], **over); cfg = model.merged(te)
    d0 = cfg.get("d0", 0)
    G = path_values(seed, c, cfg)
    r = solve_oracle(G, cfg, starts=[[d - d0 for d in s] for s in starts] if starts else None)
    none = model.simulate("none", {}, c, seed, cfg=cfg)["net"]
    sched = [(d0 + t, rows) for t, rows in r["sched"]]
    rep = model.simulate("replay", dict(sched=dict(sched)), c, seed, cfg=cfg); diff = abs(rep["net"] - r["value"]); took = False
    if inc:
        isch = [(int(d), sorted(int(i) for i in rows)) for d, rows in inc if len(rows)]
        irep = model.simulate("replay", dict(sched=dict(isch)), c, seed, cfg=cfg)
        if irep["net"] > rep["net"] and not schedule_violations(isch, cfg):
            sched, rep, diff, took = isch, irep, 0.0, True
    return dict(key=f"{site}|{c}|{f}", seed=seed, none=none, net=rep["net"], value=rep["net"] - none, upper=r["upper"] - none, table_diff=diff, n_clean=rep["n_clean"], n_missions=rep["n_missions"],
                violations=schedule_violations(sched, cfg), runtime=time.time() - t0, sched=sched, incumbent_kept=took)


def collect(rows: list[dict[str, Any]], seeds: list[int]) -> dict[str, Any]:
    """Per-case record from per-seed units, in seed order."""
    by = {r["seed"]: r for r in rows}; o = [by[s] for s in seeds]
    return {k: [r[k] for r in o] for k in ("none", "value", "upper", "n_clean", "n_missions", "violations", "table_diff", "runtime", "sched")}


def oracle_job(S: Study) -> dict[str, Any]:
    """Oracle schedules and values (results_r6_oracle.json). Units are saved as they finish, so a stopped run resumes. A seed where a tuned policy beats the oracle's schedule is solved again from that policy's mission nights."""
    t0 = time.time(); sites = sites_of(S); seeds = list(S.params.get("seeds") or S.protocol.test); over = S.params.get("over", {})
    part = S.out_path(S.output + ".partial.jsonl"); done: dict[tuple, dict[str, Any]] = {}
    if os.path.exists(part):
        for line in open(part):
            r = json.loads(line); done[(r["key"], r["seed"])] = r
    todo = [(s, c, f, x, None, over) for s, c, f in cases(sites) for x in seeds if (f"{s}|{c}|{f}", x) not in done]
    with S.runner_pool() as rn:
        with open(part, "a") as out:
            for r in rn.imap_unordered(oracle_unit, todo, chunksize=1):
                done[(r["key"], r["seed"])] = r
                out.write(json.dumps(r, default=float) + "\n"); out.flush()
        again = []
        if not over:
            st = stored_records(S)
            for (k, x), r in done.items():
                t = st[k]["test"]["F2"]; i = list(rn.test).index(x)
                best = max(POLICIES, key=lambda p: t[p]["net"][i])
                if t[best]["net"][i] > r["none"] + r["value"] + 1e-6:
                    s, c, f = k.split("|")
                    te, tr = overs(s, f)
                    sc = job((best, t[best]["params"], c, x, "site", 0.01, 1.0, dict(te, _inp=dict(tr))))[1]["sched"]
                    again.append((s, c, f, x, [[d for d, _ in sc]], over, [(int(d), list(rows)) for d, rows in sc]))
            for r in rn.imap_unordered(oracle_unit, again, chunksize=1):
                old = done[(r["key"], r["seed"])]
                r["resolved_from_policy"] = True
                if r["value"] > old["value"]:
                    done[(r["key"], r["seed"])] = r
    rows = {}
    for s, c, f in cases(sites):
        k = f"{s}|{c}|{f}"
        rows[k] = dict(site=s, market=market_of(s), contract=c, fold=f, test_year=fold_test_year(f), seeds=seeds, **collect([done[(k, x)] for x in seeds], seeds))
    meta = dict(label="MAIN-R6", seeds=seeds, units=len(done), solved_again=len(again), workers=S.protocol.workers, runtime_s_last=time.time() - t0)
    os.remove(part)
    return dict(_meta=meta, rows=rows)


def plain_job(S: Study) -> dict[str, Any]:
    """The plain loss threshold, tuned again on the same years and checked against the stored records (results_r6_plain.json)."""
    t0 = time.time(); sites = sites_of(S); st = stored_records(S); rows: dict[str, Any] = {}
    with S.runner_pool() as rn:
        for s, c, f in cases(sites):
            te, tr = overs(s, f); k = f"{s}|{c}|{f}"; o = st[k]
            best = rn.tune(c, tr, ["threshold"])["threshold"]
            ev = rn.evaluate(c, dict(threshold=best["params"], ft=o["tuned"]["F2"]["ft"]["params"]), te, tr, ["threshold", "ft"])
            same = bool(best["params"] == o["tuned"]["F2"]["threshold"]["params"] and np.array_equal(ev["threshold"]["net"], o["test"]["F2"]["threshold"]["net"]) and np.array_equal(ev["ft"]["net"], o["test"]["F2"]["ft"]["net"]))
            none = np.array(ev["none"]["net"])
            rows[k] = dict(site=s, market=market_of(s), contract=c, fold=f, test_year=fold_test_year(f), params=best["params"], train_mean=best["train_mean"], matches_stored=same, net=ev["threshold"]["net"], n_clean=ev["threshold"]["n_clean"],
                           value=float(np.mean(np.array(ev["threshold"]["net"]) - none)), ft_value=float(np.mean(np.array(ev["ft"]["net"]) - none)), ft_minus_plain=paired(ev["ft"]["net"], ev["threshold"]["net"]))
    return dict(_meta=dict(label="MAIN-R6", all_match_stored=all(r["matches_stored"] for r in rows.values()), workers=S.protocol.workers, runtime_s_last=time.time() - t0), rows=rows)


def seeds_job(S: Study) -> dict[str, Any]:
    """Three extra tuning-seed sets with per-replicate differences, for all case-years, because earlier files keep only summaries (results_r6_seeds.json). R3 and R4 means must match the stored checks."""
    t0 = time.time(); sites = sites_of(S); sets = S.params["retune"]; rows: dict[str, Any] = {k: {} for k in map("|".join, cases(sites))}; worst = 0.0
    r3 = S.stored("r3_checks.json")["retune"]; r4 = S.stored("results_r4_seeds.json")["sets"]; mk = {v: k for k, v in MARKET_SITES.items()}
    with S.runner_pool() as rn:
        for name, seeds in sets.items():
            q = rn.with_(train=seeds)
            for s, c, f in cases(sites):
                rec = run_case(q, s, c, f, "DESCRIPTIVE"); t = rec["test"]["F2"]; k = f"{s}|{c}|{f}"
                rows[k][name] = dict(d=list(np.subtract(t["proposed"]["net"], t["ft"]["net"])), planner=t["proposed"]["params"], ft=t["ft"]["params"], cmp=rec["cmp"]["planner-ft|F2"])
                old = r3[name]["rows"][f"{mk[s]}|{c}|{f}"]["cmp"]["planner-ft|F2"]["mean"] if s in mk else r4[name]["rows"][k]["planner_ft"]["mean"] if k in r4[name]["rows"] else None
                if old is not None:
                    worst = max(worst, abs(old - rec["cmp"]["planner-ft|F2"]["mean"]))
    return dict(_meta=dict(label="DESCRIPTIVE", retune=sets, max_abs_diff_vs_stored=worst, workers=S.protocol.workers, runtime_s_last=time.time() - t0), rows=rows)
