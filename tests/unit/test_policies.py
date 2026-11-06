import numpy as np
import pytest
from pvclean import model, policies


@pytest.mark.parametrize("name,par", [("fixed", {"T": 14}), ("threshold", {"theta": 0.05}), ("econ", {"b": 4}), ("ft", {"Hb": 14, "b": 2, "antic": 1}), ("proposed", {"beta": 0.5, "kappa": 0.5}),
                                      ("proposed_noval", {"beta": 0.5, "kappa": 0.5}), ("proposed_nobatch", {"b": 4})])
def test_schedules_are_feasible(name, par):
    c, v, p = model.planner_inputs("merchant")
    r = model.simulate(name, par, "merchant", 2, clim=c, vexp=v, pbar=p)
    assert r["n_clean"] > 0 and model.schedule_violations(r["sched"], model.CONFIG) == 0


def test_registry_names_match_classes():
    assert all(cls.name == k for k, cls in policies.REGISTRY.items())


def test_only_none_skips_patrols():
    assert [k for k, c in policies.REGISTRY.items() if not c.inspects] == ["none"]


def test_interval_policy_waits():
    c, v, p = model.planner_inputs("fixed")
    days = [d for d, _ in model.simulate("fixed", {"T": 40}, "fixed", 0, cfg=dict(model.CONFIG, blackouts=()), clim=c, vexp=v, pbar=p)["sched"]]
    assert len(days) >= 1 and np.diff(days).min() >= 1
