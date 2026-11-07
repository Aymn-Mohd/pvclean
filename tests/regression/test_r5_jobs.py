"""The R5 jobs on a short horizon with 2 seeds, and the plant rules of the new sites."""
import json
import os
import numpy as np
import pytest
from pvclean.data import data_path, repo_root
from pvclean.sites import load_site
from pvclean.studies import load_study, r4, r5, runner_function

ROOT = repo_root()
GRIDS = dict(fixed=[dict(T=14)], threshold=[dict(theta=0.05)], econ=[dict(b=4)], proposed=[dict(beta=0.5, kappa=1)], ft=[dict(Hb=14, b=4, antic=0)])


def has_sites():
    return os.path.exists(data_path("site_wx.npz")) and "whyalla" in np.load(data_path("site_wx.npz")).files


needs_data = pytest.mark.skipif(not has_sites(), reason="R5 weather not in the cache: run `python -m pvclean download nasa-power`")


def small(name, tmp_path):
    S = load_study(os.path.join(ROOT, "configs", "studies", f"r5_{name}.yaml"), str(tmp_path), workers=4)
    S.protocol = S.protocol.with_(train=[1000, 1001], test=[0, 1], grids=dict(S.protocol.grids, **GRIDS))
    S.params["sites"] = ["whyalla"]
    return S


@needs_data
@pytest.mark.parametrize("name,contract", [("merchant", "merchant"), ("ppa", "ppa")])
def test_contract_job_runs_one_contract(name, contract, tmp_path, monkeypatch):
    base = r4.site_over
    monkeypatch.setattr(r4, "site_over", lambda s, y, soil=0.0030: dict(base(s, y, soil), d1=60))
    S = small(name, tmp_path)
    out = json.loads(json.dumps(runner_function(S.runner)(S), default=float))
    assert len(out["r5"]) == 2 and all(v["contract"] == contract and v["site"] == "whyalla" for v in out["r5"].values())
    assert set(out["r5_meta"]["soiling_loss_pct"]) == {"whyalla|2024", "whyalla|2025"}


def test_new_sites_follow_the_r3_plant_rules():
    for s in r5.R5_SITES:
        y = load_site(s); ref = load_site({"ES_raw": "seville", "SA1_raw": "adelaide", "QLD1_raw": "brisbane"}[y["market"]])
        assert (y["tilt"], y["azimuth"], y["tz"], y["time_base"], y["weather_source"]) == (ref["tilt"], ref["azimuth"], ref["tz"], ref["time_base"], ref["weather_source"])
        assert (y["azimuth"] == 180.0) == (y["lat"] > 0)
