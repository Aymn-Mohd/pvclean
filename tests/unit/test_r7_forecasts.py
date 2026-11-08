"""FHW (weekday/weekend rolling forecast): calendar, causality, and no change to the other forecasts."""
import numpy as np
import pytest
from pvclean.forecasts import fc_value
from pvclean.forecasts.roll_hw import RollingDayType


def series(days, seed=0):
    return np.random.default_rng(seed).random(24 * days)


def test_fhw_uses_only_past_days_of_the_same_type():
    val = series(60); dt = np.zeros(60, bool); dt[5::7] = True; dt[6::7] = True
    d = 40; hh = np.arange(24 * d, 24 * d + 48)
    f = RollingDayType().predict(d, hh, val[:24 * d], None, 1, 28, day_type=dt)
    past = val[24 * (d - 28):24 * d].reshape(28, 24); pt = dt[d - 28:d]
    for k, day in enumerate((d, d + 1)):
        want = past[pt == dt[day]].mean(0)
        assert np.allclose(f[24 * k:24 * k + 24], want)


def test_fhw_is_causal_through_fc_value():
    val = series(365); warm = series(28, 1); dt = np.zeros(28 + 365, bool); dt[::7] = True
    d = 100; hh = np.arange(24 * d, 24 * d + 24 * 7)
    a = fc_value("roll_hw", d, hh, val, np.zeros_like(val), 1, warm, 28, day_type=dt)
    v2 = val.copy(); v2[24 * d:] = 99.0
    b = fc_value("roll_hw", d, hh, v2, np.zeros_like(val), 1, warm, 28, day_type=dt)
    assert np.array_equal(a, b)


def test_fhw_needs_the_calendar():
    with pytest.raises(ValueError):
        RollingDayType().predict(10, np.arange(240, 264), series(10), None, 1, 28)


def test_day_type_leaves_other_forecasts_unchanged():
    val = series(365); warm = series(28, 1); hh = np.arange(2400, 2400 + 168); dt = np.ones(28 + 365, bool)
    for m in ("roll", "dayahead", "perfect"):
        assert np.array_equal(fc_value(m, 100, hh, val, np.zeros_like(val), 1, warm, 28), fc_value(m, 100, hh, val, np.zeros_like(val), 1, warm, 28, day_type=dt))


def test_cluster_median_ci():
    from pvclean.stats import cluster_median_ci
    x = [1.0, 2.0, 3.0, 10.0, 11.0, 12.0]; c = ["a", "a", "a", "b", "b", "b"]
    r = cluster_median_ci(x, c, B=500, seed=0)
    assert r["median"] == 6.5 and r["clusters"] == 2 and r["lo"] == 2.0 and r["hi"] == 11.0
    assert r == cluster_median_ci(x, c, B=500, seed=0)
