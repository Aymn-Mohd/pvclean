import numpy as np
import pytest
from pvclean import forecasts as f

VAL = np.arange(8760, dtype=float); VEXP = np.full(8760, -1.0); HH = np.arange(240, 240 + 48)


def test_cutoffs():
    assert [f.info_cutoff(m, 10, 48) for m in ("clim", "roll", "dayahead", "perfect")] == [0, 240, 264, 288]


@pytest.mark.parametrize("mode", ["roll", "dayahead", "clim"])
def test_no_lookahead(mode):
    cut = f.info_cutoff(mode, 10, 48)
    poisoned = VAL.copy(); poisoned[cut:] = np.nan
    assert np.array_equal(f.value_forecast(mode, 10, HH, VAL, VEXP, min_hist=1), f.value_forecast(mode, 10, HH, poisoned, VEXP, min_hist=1))


def test_roll_falls_back_before_min_hist():
    assert np.all(f.value_forecast("roll", 3, HH, VAL, VEXP, min_hist=7) == -1.0)


def test_dayahead_knows_today():
    assert np.array_equal(f.value_forecast("dayahead", 10, HH, VAL, VEXP, min_hist=1)[:24], VAL[240:264])


def test_warm_up_counts_as_history():
    warm = np.full(24 * 28, 5.0)
    assert np.all(f.fc_value("roll", 0, np.arange(24), VAL, VEXP, 1, warm) == 5.0)


def test_scenarios():
    assert f.SCENARIOS["F2"] == "roll" and f.DEPLOYABLE["F4"] is False and f.DEPLOYABLE["F2"] is True


def test_unknown():
    with pytest.raises(ValueError):
        f.info_cutoff("x", 1, 1)
