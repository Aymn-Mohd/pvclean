import numpy as np
from pvclean import model
from pvclean.core import plant


def test_clipping_at_inverter_share():
    ac = plant.row_ac(np.array([2.0, 0.1]), np.array([1.0]), model.CONFIG)
    assert ac[0, 0] == model.CONFIG["row_kwp"] / model.CONFIG["dc_ac"] and ac[0, 1] < ac[0, 0]


def test_export_limit_only_when_capped():
    ac = np.full((40, 1), 20.0)
    assert plant.delivered(ac, model.CONFIG, False)[0] == 800.0
    assert plant.delivered(ac, model.CONFIG, True)[0] == plant.export_limit(model.CONFIG) == 600.0


def test_dc_power_never_negative_and_falls_with_heat():
    cfg = model.CONFIG; poa = np.array([0.0, 800.0, 800.0])
    p = plant.dc_power(poa, np.array([20.0, 20.0, 45.0]), 3.0, cfg)
    assert p[0] == 0 and p[1] > p[2] > 0


def test_clear_sky_is_cached():
    assert plant.clear_sky(model.CONFIG) is plant.clear_sky(dict(model.CONFIG))
