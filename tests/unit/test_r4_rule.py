"""The R4 decision rule and the cluster bootstrap."""
import numpy as np
import pytest
from pvclean.stats import cluster_spearman, dry_prediction, dry_rule


@pytest.mark.parametrize("days,want", [(120, "+"), (119, None), (71, None), (70, "<=0"), (0, "<=0"), (300, "+")])
def test_prediction_bands(days, want):
    assert dry_prediction(days) == want


def side(n, days, mean):
    return [(days, mean)] * n


def test_supported_at_80_percent():
    r = dry_rule(side(4, 150, 1.0) + side(4, 40, -1.0) + side(2, 40, 1.0))
    assert r["verdict"] == "SUPPORTED" and r["share_correct"] == 0.8 and r["n_correct"] == 8


def test_not_supported_at_60_percent():
    r = dry_rule(side(3, 150, 1.0) + side(3, 40, -1.0) + side(1, 150, -1.0) + side(3, 40, 1.0))
    assert r["verdict"] == "NOT SUPPORTED" and r["share_correct"] == 0.6


def test_partial_between():
    assert dry_rule(side(4, 150, 1.0) + side(3, 40, -1.0) + side(3, 40, 1.0))["verdict"] == "PARTIAL"


def test_descriptive_when_a_side_is_thin():
    r = dry_rule(side(3, 150, 1.0) + side(10, 40, -1.0))
    assert r["verdict"] == "DESCRIPTIVE" and r["n_predicted_pos"] == 3


def test_tie_counts_as_nonpositive_and_unpredicted_rows_are_left_out():
    r = dry_rule(side(4, 150, 1.0) + side(4, 40, 0.0) + side(5, 100, -9.0))
    assert r["verdict"] == "SUPPORTED" and r["share_correct"] == 1.0 and r["n_no_prediction"] == 5


def test_cluster_bootstrap_is_seeded_and_exact_rho():
    x = np.repeat(np.arange(8.0), 4); y = x + np.tile([0.1, 0.2, 0.3, 0.4], 8); c = np.repeat(list("abcdefgh"), 4)
    a = cluster_spearman(x, y, c, B=200); b = cluster_spearman(x, y, c, B=200)
    assert a == b and a["clusters"] == 8 and a["lo"] <= a["hi"] and a["rho"] > 0.9


def test_cluster_bootstrap_drops_constant_resamples():
    a = cluster_spearman([1, 1, 2, 2], [1, 2, 3, 4], ["a", "a", "b", "b"], B=200)
    assert a["dropped"] > 0 and a["B"] == 200
