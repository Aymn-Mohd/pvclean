import numpy as np
import pytest
from pvclean import model
from pvclean.core.world import World

INP = {}


def inp(c="merchant"):
    if c not in INP:
        INP[c] = model.planner_inputs(c)
    return INP[c]


def run(pol, par, c="merchant", seed=0, **k):
    i = inp(c)
    return model.simulate(pol, par, c, seed, clim=i[0], vexp=i[1], pbar=i[2], **k)


def test_none_has_no_cost():
    r = run("none", {})
    assert r["n_clean"] == 0 and r["net"] == r["revenue"]


def test_net_identity():
    r = run("threshold", {"theta": 0.05})
    assert r["net"] == pytest.approx(r["revenue"] - r["cost_clean"] - r["cost_mission"] - r["cost_insp"])


def test_cleaning_raises_energy():
    assert run("fixed", {"T": 14})["energy_kwh"] > run("none", {})["energy_kwh"]


def test_down_nights_drop_missions():
    a = run("fixed", {"T": 14}); b = run("fixed", {"T": 14}, cfg=dict(model.CONFIG, availability=0.5))
    assert b["n_missions"] < a["n_missions"]


def test_diag_does_not_change_decisions():
    assert run("proposed", {"beta": 0.5, "kappa": 0.5})["sched"] == run("proposed", {"beta": 0.5, "kappa": 0.5}, cfg=dict(model.CONFIG, diag=True))["sched"]


def test_world_replaces_truth():
    dry = World(weather=lambda s, c: dict(pdc=np.zeros(8760), rain=np.zeros(365), clear_pdc=None))
    assert run("none", {}, world=dry)["revenue"] == 0.0


def test_carry_returns_state():
    r = run("none", {}, cfg=dict(model.CONFIG, carry=True))
    assert set(r["state"]) == set(model.STATE_KEYS) | {"last_clean"}
