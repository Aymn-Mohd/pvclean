"""The R6 decision rules, the nested bootstrap and the oracle solver against the subset MILP."""
import numpy as np
import pytest
from pvclean import model
from pvclean.exact import path_values, row_tables, schedule_value, solve, solve_oracle
from pvclean.stats import ft_plain_rule, headroom_rule, nested_bootstrap


def test_headroom_bands():
    assert headroom_rule([0.9] * 4 + [0.5])["verdict"] == "SUPPORTED"
    assert headroom_rule([0.95] * 3 + [0.5] * 2)["verdict"] == "NOT SUPPORTED"
    assert headroom_rule([0.95] * 7 + [0.5] * 3)["verdict"] == "PARTIAL"


def r(m, lo, hi):
    return dict(mean=m, lo=lo, hi=hi)


def test_ft_plain_bands():
    up = r(5, 1, 9); dn = r(-5, -9, -1); flat = r(-1, -3, 2)
    assert ft_plain_rule([up] * 5)["verdict"] == "SUPPORTED"
    assert ft_plain_rule([up] * 4 + [flat])["verdict"] == "SUPPORTED"
    assert ft_plain_rule([up] * 4 + [dn])["verdict"] == "PARTIAL"
    assert ft_plain_rule([up] * 2 + [flat] * 2)["verdict"] == "NOT SUPPORTED"
    assert ft_plain_rule([up] * 3 + [flat] * 2)["verdict"] == "PARTIAL"


def test_nested_bootstrap_is_seeded_and_wider_with_set_spread():
    rng = np.random.default_rng(1); a = rng.normal(0, 1, (4, 50)); b = a + np.array([[-5], [0], [0], [5]])
    x, y = nested_bootstrap(a, 500), nested_bootstrap(b, 500)
    assert x == nested_bootstrap(a, 500) and y["hi"] - y["lo"] > x["hi"] - x["lo"]


@pytest.mark.parametrize("contract,seed,crow", [("merchant", 0, 4.0), ("fixed", 3, 12.0)])
def test_oracle_equals_the_subset_milp_on_a_small_instance(contract, seed, crow):
    cfg = model.merged(dict(n_rows=6, night_min=100.0, d0=120, d1=180, c_row=crow))
    Rev = row_tables(seed, contract, cfg); res, s = solve(Rev, cfg, 120); opt = schedule_value(Rev, s, cfg)
    o = solve_oracle(path_values(seed, contract, cfg), cfg)
    assert abs(o["value"] - opt) < 1e-6 and o["upper"] >= opt - 1e-6
