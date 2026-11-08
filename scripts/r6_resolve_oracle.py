"""Phase R6 fix: re-solves the oracle units where a tuned policy still beats the stored oracle schedule, with every given start searched and the policy's own schedule kept as an incumbent.
Only those units run again; results/results_r6_oracle.json is patched in place and the fix is recorded in its _meta. Run: nice -n 10 python scripts/r6_resolve_oracle.py"""
from __future__ import annotations
import json
import os
import time
from multiprocessing import Pool
import numpy as np
from pvclean.data import repo_root, results_dir
from pvclean.studies import load_study
from pvclean.studies.r6 import POLICIES, collect, oracle_unit, overs, stored_records
from pvclean.studies.runner import job


def policy_unit(a: tuple) -> tuple:
    """The best policy's schedule at one seed, rebuilt exactly as the oracle job rebuilds it."""
    k, x, best, params = a
    s, c, f = k.split("|"); te, tr = overs(s, f)
    sc = job((best, params, c, x, "site", 0.01, 1.0, dict(te, _inp=dict(tr))))[1]["sched"]
    return k, x, [(int(d), [int(i) for i in rows]) for d, rows in sc]


def main() -> None:
    t0 = time.time(); path = os.path.join(results_dir(), "results_r6_oracle.json"); D = json.load(open(path))
    S = load_study(os.path.join(repo_root(), "configs", "studies", "r6_oracle.yaml"), results_dir()); st = stored_records(S); test = list(S.protocol.test)
    todo = []
    for k, o in D["rows"].items():
        t = st[k]["test"]["F2"]
        for j, x in enumerate(o["seeds"]):
            i = test.index(x); best = max(POLICIES, key=lambda p: t[p]["net"][i])
            if t[best]["net"][i] > o["none"][j] + o["value"][j] + 1e-6:
                todo.append((k, x, best, t[best]["params"]))
    print("units to solve again:", len(todo), flush=True)
    with Pool(os.cpu_count()) as pool:
        inc = pool.map(policy_unit, todo)
        args = [(*k.split("|"), x, [[d for d, _ in sc]], {}, sc) for k, x, sc in inc]
        new = pool.map(oracle_unit, args, chunksize=1)
    log = []
    for r in new:
        o = D["rows"][r["key"]]; j = o["seeds"].index(r["seed"]); old = o["value"][j]
        log.append(dict(key=r["key"], seed=r["seed"], old_value=old, new_value=r["value"], incumbent_kept=r["incumbent_kept"], violations=r["violations"]))
        if r["value"] > old:
            for f in ("none", "value", "upper", "n_clean", "n_missions", "violations", "table_diff", "runtime", "sched"):
                o[f][j] = r[f]
    D["_meta"]["fix_resolve"] = dict(note="Re-solve of units where a tuned policy beat the stored oracle schedule: every given start searched, policy schedule kept as incumbent. See EXPERIMENT_LOG, Phase R6 run log.",
                                     units=len(new), improved=sum(x["new_value"] > x["old_value"] for x in log), incumbent_kept=sum(x["incumbent_kept"] for x in log), runtime_s=time.time() - t0, units_log=log)
    with open(path + ".tmp", "w") as f:
        json.dump(D, f, default=float)
    os.replace(path + ".tmp", path)
    print(json.dumps({k: v for k, v in D["_meta"]["fix_resolve"].items() if k != "units_log"}), flush=True)
    for x in log:
        print(x["key"], x["seed"], f"{x['old_value']:.2f} -> {x['new_value']:.2f}", "incumbent" if x["incumbent_kept"] else "search", flush=True)


if __name__ == "__main__":
    np.seterr(all="ignore"); main()
