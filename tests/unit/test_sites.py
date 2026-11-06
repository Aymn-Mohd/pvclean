import pytest
from pvclean import sites


@pytest.mark.parametrize("name", list(sites.REGISTRY))
def test_site_files_are_complete(name):
    s = sites.load_site(name)
    assert {"lat", "lon", "tilt", "azimuth", "tz", "market", "weather_source"} <= set(s) and s["name"] == name


def test_north_facing_in_the_south():
    assert sites.load_site("adelaide")["azimuth"] == 0.0 and sites.load_site("seville")["azimuth"] == 180.0


def test_measured_sites_have_a_price_clock():
    assert sites.site_params("seville")["time_base"] == "Europe/Madrid" and "time_base" not in sites.site_params("dubai")
