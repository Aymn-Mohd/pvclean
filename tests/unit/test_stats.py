import numpy as np
import pytest
from pvclean import stats


def test_ci95_single_value():
    assert stats.ci95([3.0]) == (3.0, 0.0)


def test_paired_counts_wins():
    r = stats.paired([1, 2, 3], [0, 2, 4])
    assert r["mean"] == 0.0 and r["wins"] == 1 and r["lo"] < 0 < r["hi"] and r["n"] == 3


def test_paired_summary_is_seeded():
    assert stats.paired_summary([1.0, 2.0, 4.0]) == stats.paired_summary([1.0, 2.0, 4.0])


def test_decomposition_identity():
    A = dict(net=[9.0, 8.0], revenue=[12.0, 11.0], energy_kwh=[100.0, 90.0], cost_clean=[2.0, 2.0], cost_mission=[1.0, 1.0], cost_insp=[0.0, 0.0], n_clean=[1, 1], n_missions=[1, 1], params={})
    B = dict(net=[5.0, 5.0], revenue=[5.0, 5.0], energy_kwh=[50.0, 50.0], cost_clean=[0.0, 0.0], cost_mission=[0.0, 0.0], cost_insp=[0.0, 0.0], n_clean=[0, 0], n_missions=[0, 0], params={})
    d = stats.decomp(A, B, [0.1, 0.1])
    assert d["identity_max_abs_residual"] == 0.0 and d["quantity"]["mean"] == pytest.approx(4.5) and d["timing"]["mean"] == pytest.approx(2.0)


def row(m, lo, hi):
    return dict(mean=m, lo=lo, hi=hi)


def test_tally_rule_edges():
    pos = [row(1, 0.5, 2)]; neg = [row(-1, -2, -0.5)]; span = [row(-1, -2, 1)]
    assert stats.tally_rule(pos * 10 + span * 2)["verdict"] == "SUPPORTED"
    assert stats.tally_rule(pos * 11 + neg)["verdict"] == "PARTIAL"
    assert stats.tally_rule(pos * 6 + neg * 6)["verdict"] == "NOT SUPPORTED"
    assert stats.tally_rule(pos * 7 + span * 5)["verdict"] == "PARTIAL"


def test_exact_zero_counts_as_at_or_below():
    assert stats.tally_rule([row(0.0, 0.0, 0.0)])["mean_nonpos"] == 1


def test_interval_rule():
    assert stats.interval_rule([row(1, 0.5, 2)] * 6 + [row(0.1, -1, 1)] * 6)["verdict"] == "SUPPORTED"
    assert stats.interval_rule([row(-1, -2, 1)] * 6 + [row(1, -1, 2)] * 6)["verdict"] == "NOT SUPPORTED"


def test_robust_rule():
    assert stats.robust_rule(row(1, 0.5, 2), row(0.2, -1, 2)) == "ROBUST"
    assert stats.robust_rule(row(1, 0.5, 2), row(-0.2, -1, 2)) == "NOT ROBUST"
    assert stats.robust_rule(row(1, 0.5, 2), row(1, -3, -1)) == "NOT ROBUST"
