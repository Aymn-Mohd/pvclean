import numpy as np
from pvclean import model
from pvclean.core import soiling

C = model.CONFIG


def test_exposure_mean_one_and_gradient():
    e = soiling.exposure(C)
    assert abs(e.mean() - 1) < 1e-12 and e[:5].mean() > e[-5:].mean()
    assert np.array_equal(soiling.exposure(C, hetero=0.0), np.ones(C["n_rows"]))


def test_dust_is_seeded():
    a, b = soiling.dust(3, C), soiling.dust(3, C)
    assert np.array_equal(a[0], b[0]) and not np.array_equal(a[0], soiling.dust(4, C)[0]) and a[1].shape == (365, 40)


def test_rain_recovery_thresholds():
    assert soiling.rain_recovery(0.5, C) == 0.0 and soiling.rain_recovery(1.0, C) == 0.2 and soiling.rain_recovery(5.0, C) == 0.9


def test_season_shift_moves_peak():
    a = soiling.expected_increment(C)
    assert 150 < int(np.argmax(a)) < 190


def test_rain_forecast_flags_shape():
    f = soiling.rain_forecast(np.zeros(365), 1, C)
    assert f.dtype == bool and 0 < f.mean() < 0.15
