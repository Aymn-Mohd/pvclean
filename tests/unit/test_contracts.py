import numpy as np
import pytest
from pvclean import contracts, model

SPOT = np.tile(np.array([0.1, -0.05, 0.0]), 2920)


def test_values():
    assert contracts.hourly_value("fixed", SPOT, model.CONFIG)[1] == 0.06
    assert list(contracts.hourly_value("merchant", SPOT, model.CONFIG)[:3]) == [0.1, 0.0, 0.0]
    assert list(contracts.hourly_value("ppa", SPOT, model.CONFIG)[:3]) == [0.05, 0.0, 0.05]


def test_only_capped_limits_export():
    assert [n for n, c in contracts.REGISTRY.items() if c.capped] == ["capped"]


def test_interval_keys():
    assert contracts.get_contract("merchant").interval_key == "merchant" and contracts.get_contract("ppa").interval_key == "ppa_frac" and contracts.get_contract("fixed").interval_key is None


def test_unknown():
    with pytest.raises(ValueError):
        contracts.get_contract("x")
