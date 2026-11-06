import numpy as np
import pandas as pd
from pvclean import markets, model
from pvclean.markets.build import interval_stats, old_style


def test_generated_is_seeded():
    assert np.array_equal(model.spot_prices(1), model.spot_prices(1)) and not np.array_equal(model.spot_prices(1), model.spot_prices(2))


def test_depression_scale_lowers_midday():
    assert model.spot_prices(1, model.merged({"price_depress_scale": 3.0})).mean() < model.spot_prices(1).mean()


def test_contract_value_generated_has_no_warm_up():
    v, w = markets.contract_value("merchant", 0, model.CONFIG)
    assert w is None and v.min() >= 0


def test_interval_stats_keeps_negative_intervals_visible():
    h = interval_stats(np.array([0, 0, 0, 0]), np.array([10.0, -10.0, 10.0, -10.0]))
    assert h["mean"][0] == 0.0 and h["merchant"][0] == 5.0 and h["ppa_frac"][0] == 0.5 and h["neg_share"][0] == 0.5


def test_old_style():
    m, f = old_style(np.array([1.0, -1.0]))
    assert list(m) == [1.0, 0.0] and list(f) == [1.0, 0.0]
