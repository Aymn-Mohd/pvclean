"""The R4 jobs on a short horizon with 2 seeds, and one stored R3 case reproduced through the R4 code path."""
import json
import os
import numpy as np
import pytest
from pvclean.data import repo_root, results_dir
from pvclean.sites import load_site, site_config
from pvclean.stats import dry_rule
from pvclean.studies import load_study, runner_function
from pvclean.studies import matched, r4

ROOT = repo_root()
GRIDS = dict(fixed=[dict(T=14)], threshold=[dict(theta=0.05)], econ=[dict(b=4)], proposed=[dict(beta=0.5, kappa=1)], ft=[dict(Hb=14, b=4, antic=0)])
JOBS = ["sites", "shift", "lowsoil", "cost", "seeds"]


def has_new_sites():
    from pvclean.data import data_path
    return os.path.exists(data_path("site_wx.npz")) and "bilbao" in np.load(data_path("site_wx.npz")).files


needs_data = pytest.mark.skipif(not has_new_sites(), reason="R4 weather not in the cache: run `python -m pvclean download nasa-power`")


def small(name, tmp_path):
    S = load_study(os.path.join(ROOT, "configs", "studies", f"r4_{name}.yaml"), str(tmp_path), workers=4)
    S.protocol = S.protocol.with_(train=[1000, 1001], test=[0, 1], grids=dict(S.protocol.grids, **GRIDS))
    S.params["sites"] = ["bilbao"]
    if name == "seeds":
        S.params["retune"] = dict(train1005=[1005, 1006])
    return S


@pytest.fixture
def short(monkeypatch):
    base = r4.site_over
    monkeypatch.setattr(r4, "site_over", lambda s, y, soil=0.0030: dict(base(s, y, soil), d1=60))


@needs_data
@pytest.mark.parametrize("name", JOBS)
def test_job_runs_on_a_short_horizon(name, tmp_path, short):
    S = small(name, tmp_path)
    out = json.loads(json.dumps(runner_function(S.runner)(S), default=float))
    if name == "sites":
        assert len(out["r4"]) == 4 and all(v["site"] == "bilbao" and len(v["test"]["F2"]["ft"]["net"]) == 2 and list(v["cmp"]).count("planner-ft|F2") == 1 for v in out["r4"].values())
        assert set(out["r4_meta"]["soiling_loss_pct"]) == {"bilbao|2024", "bilbao|2025"}
    elif name == "cost":
        assert set(out["arms"]) == {"x0.5", "x2"} and all(a["tally"]["n"] == 4 for a in out["arms"].values())
    elif name == "seeds":
        assert out["sets"]["train1005"]["tally"]["n"] == 4
    else:
        assert out["tally"]["n"] == 4


@needs_data
def test_cost_multiplier_reaches_the_ledger(tmp_path, short):
    S = small("cost", tmp_path)
    with S.runner_pool() as rn:
        a = r4.run_case(rn, "bilbao", "merchant", "Y2", "x", extra=dict(c_row=2.0, c_mission=5.0))["test"]["F2"]["fixed"]
        b = r4.run_case(rn, "bilbao", "merchant", "Y2", "x", extra=dict(c_row=8.0, c_mission=20.0))["test"]["F2"]["fixed"]
    assert a["n_clean"] == b["n_clean"] and np.allclose(np.array(b["cost_clean"]), 4 * np.array(a["cost_clean"]))


def test_new_sites_follow_the_r3_plant_rules():
    for s in r4.NEW_SITES:
        y = load_site(s); ref = load_site({"ES_raw": "seville", "SA1_raw": "adelaide", "QLD1_raw": "brisbane"}[y["market"]])
        assert (y["tilt"], y["azimuth"], y["tz"], y["time_base"], y["weather_source"]) == (ref["tilt"], ref["azimuth"], ref["tz"], ref["time_base"], ref["weather_source"])
        assert (y["azimuth"] == 180.0) == (y["lat"] > 0)


def test_site_over_matches_r3():
    assert r4.site_over("seville", 2024) == matched.site_over("ES_raw", 2024)


@needs_data
def test_seville_through_the_r4_path_equals_stored_r3(tmp_path):
    S = load_study(os.path.join(ROOT, "configs", "studies", "r4_sites.yaml"), str(tmp_path))
    old = json.load(open(os.path.join(results_dir(), "results_matched.json")))["r3"]["soil0.30|ES_raw|merchant|Y2"]
    with S.runner_pool() as rn:
        rec = r4.run_case(rn, "seville", "merchant", "Y2", "check")
    for p in ("none", "fixed", "threshold", "econ", "ft", "proposed"):
        assert np.array_equal(rec["test"]["F2"][p]["net"], old["test"]["F2"][p]["net"]), p
    assert rec["cmp"]["planner-ft|F2"] == old["cmp"]["planner-ft|F2"]


def test_stored_prediction_table_matches_the_rule():
    rain = json.load(open(os.path.join(results_dir(), "r4_rain.json")))["sites"]
    days = [v["longest_run_without_5mm"] for s in rain.values() for v in s["years"].values()]
    r = dry_rule([(d, 1.0) for d in days for _ in range(2)])
    assert (r["n_predicted_pos"], r["n_predicted_nonpos"], r["n_no_prediction"]) == (14, 4, 2)
