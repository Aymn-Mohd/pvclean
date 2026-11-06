import numpy as np
import pandas as pd
from pvclean import model, weather


def test_source_selection():
    assert weather.source_of({}) == "generated" and weather.source_of({"wx_years": (2002,)}) == "nasa_dubai" and weather.source_of({"wx_site": "x"}) == "nasa_site"
    assert weather.source_of({"wx_site": "x", "weather_source": "generated"}) == "generated"


def test_generated_shapes():
    w = model.weather(0)
    assert w["pdc"].shape == (8760,) and w["rain"].shape == (365,) and w["pdc"].min() >= 0


def test_rain_scale_adds_rain_days():
    assert (model.weather(1, model.merged({"rain_scale": 3.0}))["rain"] > 0).sum() >= (model.weather(1)["rain"] > 0).sum()


def test_time_base_sums_local_days():
    t = pd.date_range("2024-12-30", "2026-01-03", freq="1h", tz="UTC", inclusive="left")
    out, stamps, n = weather.to_time_base(t, np.ones(len(t)), "Etc/GMT-10", 2025, "sum")
    assert out.shape == (365,) and np.all(out == 24) and np.all(n == 24)


def test_dst_days_have_true_hours():
    t = pd.date_range("2024-12-30", "2026-01-03", freq="1h", tz="UTC", inclusive="left")
    n = weather.to_time_base(t, np.ones(len(t)), "Europe/Madrid", 2025, "hours")[2]
    assert sorted(set(n)) == [23, 24, 25]
