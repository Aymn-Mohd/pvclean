import numpy as np
from pvclean import model


def test_inputs_use_config_seeds():
    a = model.climatology_pdc(); b = model.climatology_pdc(model.CONFIG, range(2000, 2010))
    assert np.array_equal(a, b) and a.shape == (8760,)


def test_vexp_is_month_hour_mean():
    c, v, p = model.planner_inputs("merchant")
    assert v.shape == (8760,) and p > 0 and v[0] == v[24]


def test_fixed_contract_price_is_tariff():
    assert abs(model.planner_inputs("fixed")[2] - model.CONFIG["tariff"]) < 1e-12
