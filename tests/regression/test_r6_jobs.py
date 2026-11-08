"""The R6 jobs on a short horizon with 2 seeds, and the oracle against the simulator."""
import json
import os
import numpy as np
import pytest
from pvclean import model
from pvclean.data import data_path, repo_root, results_dir
from pvclean.exact import path_values
from pvclean.studies import load_study, r4, r6, runner_function

ROOT = repo_root()
GRIDS = dict(fixed=[dict(T=14)], threshold=[dict(theta=0.05)], econ=[dict(b=4)], proposed=[dict(beta=0.5, kappa=1)], ft=[dict(Hb=14, b=4, antic=0)])


def has_sites():
    return os.path.exists(data_path("site_wx.npz")) and "whyalla" in np.load(data_path("site_wx.npz")).files


needs_data = pytest.mark.skipif(not has_sites(), reason="R6 weather not in the cache: run `python -m pvclean download nasa-power`")


def study(name, tmp_path, small=True):
    S = load_study(os.path.join(ROOT, "configs", "studies", f"r6_{name}.yaml"), str(tmp_path), workers=4)
    if small:
        S.protocol = S.protocol.with_(train=[1000, 1001], test=[0, 1], grids=dict(S.protocol.grids, **GRIDS))
    S.params["sites"] = ["bilbao"]
    return S


@needs_data
def test_oracle_job_on_a_short_horizon(tmp_path):
    S = study("oracle", tmp_path); S.params["over"] = dict(d1=60); S.params["seeds"] = [0, 1]
    out = json.loads(json.dumps(runner_function(S.runner)(S), default=float))
    assert len(out["rows"]) == 4 and not os.path.exists(S.out_path(S.output + ".partial.jsonl"))
    for r in out["rows"].values():
        assert len(r["value"]) == 2 and sum(r["violations"]) == 0 and max(r["table_diff"]) < 1e-6
        assert all(u >= v - 1e-6 and v >= -1e-9 for u, v in zip(r["upper"], r["value"]))


@needs_data
def test_plain_job_matches_the_stored_records(tmp_path):
    S = study("plain", tmp_path, small=False)
    out = runner_function(S.runner)(S)
    assert out["_meta"]["all_match_stored"] and len(out["rows"]) == 4


@needs_data
def test_seeds_job_keeps_per_replicate_differences(tmp_path, monkeypatch):
    base = r4.site_over
    monkeypatch.setattr(r4, "site_over", lambda s, y, soil=0.0030: dict(base(s, y, soil), d1=60))
    S = study("seeds", tmp_path); S.params["retune"] = dict(train1005=[1005, 1006])
    out = runner_function(S.runner)(S)
    assert all(len(v["train1005"]["d"]) == 2 for v in out["rows"].values())


@needs_data
def test_path_tables_equal_the_simulator_for_a_tuned_policy():
    te, tr = r6.overs("bilbao", "Y2"); cfg = model.merged(te)
    G = path_values(0, "merchant", cfg)
    assert abs(G[:, 0, 365].sum() - model.simulate("none", {}, "merchant", 0, cfg=cfg)["net"]) < 1e-6
    sched = {50: [0, 1, 2], 90: [1, 3]}
    r = model.simulate("replay", dict(sched=sched), "merchant", 0, cfg=cfg)
    seq = {i: [0] for i in range(cfg["n_rows"])}
    for d, rows in sched.items():
        for i in rows:
            seq[i].append(d)
    rev = sum(G[i, a, b] for i, s in seq.items() for a, b in zip(s, s[1:] + [365]))
    assert abs(rev - r["revenue"]) < 1e-6 and r["n_clean"] == 5 and r["n_missions"] == 2


@needs_data
def test_oracle_keeps_a_better_incumbent_and_searches_every_start():
    """The oracle is at least any feasible schedule it is given: a policy's schedule passed as incumbent is never beaten by the stored result (Phase R6 fix)."""
    te, tr = r6.overs("bilbao", "Y2"); cfg = model.merged(dict(te, d1=60))
    inc = [(20, list(range(cfg["n_rows"]))[:3]), (40, [0, 1])]
    r = r6.oracle_unit(("bilbao", "merchant", "Y2", 0, [[d for d, _ in inc]], dict(d1=60), inc))
    rep = model.simulate("replay", dict(sched=dict(inc)), "merchant", 0, cfg=cfg)
    assert r["violations"] == 0 and r["net"] >= rep["net"] - 1e-6 and r["upper"] >= r["value"] - 1e-6
