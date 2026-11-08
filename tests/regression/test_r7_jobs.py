"""The R7 jobs on a short horizon with 2 seeds."""
import json
import os
import numpy as np
import pytest
from pvclean.data import data_path, repo_root
from pvclean.studies import load_study, r7, runner_function

ROOT = repo_root()
GRIDS = dict(fixed=[dict(T=14)], threshold=[dict(theta=0.05)], econ=[dict(b=4)], proposed=[dict(beta=0.5, kappa=1), dict(beta=0.5, kappa=float("inf"))], ft=[dict(Hb=14, b=4, antic=0)])


def has_sites():
    return os.path.exists(data_path("site_wx.npz")) and "whyalla" in np.load(data_path("site_wx.npz")).files


needs_data = pytest.mark.skipif(not has_sites(), reason="R7 weather not in the cache: run `python -m pvclean download nasa-power`")


@pytest.fixture
def short(monkeypatch):
    base_site, base_overs = r7.site_over, r7.overs
    monkeypatch.setattr(r7, "site_over", lambda s, y, soil=0.0030: dict(base_site(s, y, soil), d1=60))
    monkeypatch.setattr(r7, "overs", lambda s, f: tuple(dict(o, d1=60) for o in base_overs(s, f)))


def study(name, tmp_path):
    S = load_study(os.path.join(ROOT, "configs", "studies", f"r7_{name}.yaml"), str(tmp_path), workers=4)
    S.protocol = S.protocol.with_(train=[1000, 1001], test=[0, 1], grids=dict(S.protocol.grids, **GRIDS))
    S.params["sites"] = ["seville"]
    return S


@needs_data
@pytest.mark.parametrize("name", ["forecast", "abstain", "dust", "rain", "cost"])
def test_arm_jobs(name, tmp_path, short):
    S = study(name, tmp_path)
    out = json.loads(json.dumps(runner_function(S.runner)(S), default=float))
    for arm in out["arms"].values():
        assert len(arm["rows"]) == 4
        for r in arm["rows"].values():
            assert all(len(v) == 2 for v in r["net"].values()) and len(r["none"]) == 2 and set(r["value"]) == {"threshold", "ft", "proposed"}
    if name == "forecast":
        A = out["arms"]; assert set(A) == {"F2", "F7d", "F56d", "FHW", "F3", "F4"}
        for k in A["F2"]["rows"]:      # the plain threshold reads no prices
            assert all(A[n]["rows"][k]["net"]["threshold"] == A["F2"]["rows"][k]["net"]["threshold"] for n in A)


@needs_data
def test_oracle_split_job(tmp_path, short):
    S = study("oracle_split", tmp_path); S.params.update(keys=["seville|merchant|Y2"], seeds=[0, 1])
    out = runner_function(S.runner)(S)
    r = out["rows"]["seville|merchant|Y2"]
    assert set(r) == {"C", "A", "B", "D"} and not os.path.exists(S.out_path(S.output + ".partial.jsonl"))
    for kd in "ABD":
        assert len(r[kd]["value"]) == 2 and sum(r[kd]["violations"]) == 0
