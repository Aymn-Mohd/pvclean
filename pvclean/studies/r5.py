"""Phase R5: the R4 dry-spell rule on unseen sites, merchant contract first. Every job reuses the R3 and R4 replay. Pre-registration: docs/records/decisions.md, "Phase R5"."""
from __future__ import annotations
import time
from typing import Any
import numpy as np
from pvclean.sites import site_config
from .matched import FOLD_NAMES, fold_test_year
from .r4 import F2_ONLY, _meta, market_of, row, run_case, soiling_loss, tally
from .study import Study

R5_SITES = ("murcia", "badajoz", "a_coruna", "whyalla", "mount_gambier", "roma_qld")


def sites_of(S: Study) -> tuple[str, ...]:
    """The sites of a study: params `sites`, by default the six R5 sites."""
    return tuple(S.params.get("sites", R5_SITES))


def contract_job(S: Study) -> dict[str, Any]:
    """One contract at every site: full records with the schema of results_r4_sites.json, plus the soiling loss of each site-year (results_r5_merchant.json, results_r5_ppa.json)."""
    t0 = time.time(); sites = sites_of(S); c = S.params["contract"]; label = S.params["record_label"]; r: dict[str, Any] = {}
    with S.runner_pool() as rn:
        for s in sites:
            for f in FOLD_NAMES:
                r[f"soil0.30|{s}|{c}|{f}"] = run_case(rn, s, c, f, label)
        loss = {f"{s}|{fold_test_year(f)}": soiling_loss(rn, s, fold_test_year(f)) for s in sites for f in FOLD_NAMES}
    return dict(r5=r, r5_meta=_meta(S, t0, label, contract=c, sites={s: dict(site_config(s), market=market_of(s)) for s in sites}, modes=F2_ONLY, soiling_loss_pct=loss))


def kappa_job(S: Study) -> dict[str, Any]:
    """POST HOC: the wider kappa grid on both contracts (results_r5_kappa.json). Nothing but the planner may move against the stored R5 records."""
    t0 = time.time(); sites = sites_of(S); rows: dict[str, Any] = {}; moved = 0
    stored = {c: S.stored(f"results_r5_{c}.json")["r5"] for c in S.params["contracts"]}
    with S.runner_pool() as rn:
        for c in S.params["contracts"]:
            for s in sites:
                for f in FOLD_NAMES:
                    rec = run_case(rn, s, c, f, "POST HOC"); old = stored[c].get(f"soil0.30|{s}|{c}|{f}")
                    rows[f"{s}|{c}|{f}"] = row(rec)
                    if old is not None:
                        t, o = rec["test"]["F2"], old["test"]["F2"]
                        assert rec["best_baseline"] == old["best_baseline"] and np.array_equal(t["none"]["net"], o["none"]["net"]), "a baseline moved"
                        for p in ("fixed", "threshold", "econ", "ft"):
                            assert rec["tuned"]["F2"][p] == old["tuned"]["F2"][p] and np.array_equal(t[p]["net"], o[p]["net"]), f"{p} moved"
                        assert rec["tuned"]["F2"]["proposed"]["train_mean"] >= old["tuned"]["F2"]["proposed"]["train_mean"], "training mean fell on a wider grid"
                        moved += rec["tuned"]["F2"]["proposed"]["params"] != old["tuned"]["F2"]["proposed"]["params"]
    kg = S.params["kappa_grid"]
    return dict(_meta=_meta(S, t0, "POST HOC", kappa_grid=kg, planner_params_moved=int(moved), kappa_at_grid_top=sum(r["params"]["proposed"]["kappa"] == kg[-1] for r in rows.values())), rows=rows, tally=tally(rows))
