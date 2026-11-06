"""Adding a site, contract, policy, forecast or market takes one new file and one registry line. The files are in tests/examples; `register` stands for the registry line.
Nothing here edits or patches core code."""
import os
import sys
import numpy as np
import pytest
from pvclean import contracts, forecasts, markets, model, policies, sites

EX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "examples")
sys.path.insert(0, EX)
from toy_contract import TimeOfUse  # noqa: E402
from toy_forecast import Yesterday  # noqa: E402
from toy_market import FlatMarket  # noqa: E402
from toy_policy import WeeklyDirtiest  # noqa: E402


@pytest.fixture(autouse=True)
def registered():
    policies.register("weekly_dirtiest", WeeklyDirtiest); contracts.register("tou", TimeOfUse()); forecasts.register("yesterday", Yesterday()); markets.register("flat", FlatMarket())
    sites.register("toy", os.path.join(EX, "toy_site.yaml"))
    yield
    for reg, k in ((policies.REGISTRY, "weekly_dirtiest"), (contracts.REGISTRY, "tou"), (forecasts.REGISTRY, "yesterday"), (markets.REGISTRY, "flat"), (sites.REGISTRY, "toy")):
        reg.pop(k)


def run(pol, par, contract="merchant", **over):
    cfg = model.merged(over)
    c, v, p = model.planner_inputs(contract, cfg)
    return model.simulate(pol, par, contract, 1, cfg=cfg, clim=c, vexp=v, pbar=p)


def test_toy_policy():
    r = run("weekly_dirtiest", {"every": 7})
    assert r["n_missions"] == r["n_clean"] > 40 and all(len(rows) == 1 for _, rows in r["sched"])
    assert model.schedule_violations(r["sched"], model.CONFIG) == 0


def test_toy_site():
    cfg = model.merged(sites.site_params("toy"))
    assert (cfg["lat"], cfg["tz"]) == (35.0, "Asia/Nicosia")
    r = run("proposed", {"beta": 0.5, "kappa": 0.5}, **sites.site_params("toy"))
    assert r["energy_kwh"] != run("proposed", {"beta": 0.5, "kappa": 0.5})["energy_kwh"] and r["energy_kwh"] > 0


def test_toy_contract():
    assert run("fixed", {"T": 14}, contract="tou")["revenue"] > run("fixed", {"T": 14}, contract="fixed")["revenue"]


def test_toy_forecast():
    a = run("proposed", {"beta": 0.5, "kappa": 0.5}, fc_mode="yesterday", roll_min_hist=1)
    assert a["n_clean"] > 0 and forecasts.info_cutoff("yesterday", 5, 168) == 120


def test_toy_market():
    assert np.all(model.spot_prices(0, model.merged({"market": "flat"})) == 0.05)
    assert run("none", {}, market="flat")["revenue"] != run("none", {})["revenue"]
