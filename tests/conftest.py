"""Shared test settings."""
import pytest
from pvclean.data import has_data


# The tests from before the restructure read data when they are imported.
collect_ignore = [] if has_data("real_prices.npz", "real_prices_v2.npz", "site_wx.npz", "dubai_wx.npz") else ["legacy"]


@pytest.fixture(scope="session")
def data_available():
    """True if the market and weather data are in the cache."""
    return has_data("real_prices.npz", "real_prices_v2.npz", "site_wx.npz", "dubai_wx.npz")
