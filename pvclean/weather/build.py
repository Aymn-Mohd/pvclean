"""Builds the weather tables of the data cache from downloaded NASA POWER files."""
from __future__ import annotations
import io
from typing import Iterable
import numpy as np
import pandas as pd
from pvclean.data import data_path


def dubai() -> dict[int, np.ndarray]:
    """Local-time Dubai years from new/nasa_dubai.csv.gz."""
    w = pd.read_csv(data_path("new", "nasa_dubai.csv.gz"))
    t = pd.to_datetime(dict(year=w.YEAR, month=w.MO, day=w.DY, hour=w.HR)) + pd.Timedelta(hours=4)  # UTC -> Dubai
    w.index = t
    res = {}
    for y in range(2002, 2026):
        d = w[w.index.year == y]
        d = d[~((d.index.month == 2) & (d.index.day == 29))]
        assert len(d) == 8760, (y, len(d))
        res[y] = d[["ALLSKY_SFC_SW_DWN", "CLRSKY_SFC_SW_DWN", "T2M", "PRECTOTCORR"]].values
    return res


def read_power(site: str, years: Iterable[int] = range(2001, 2026)) -> pd.DataFrame:
    """Raw NASA POWER yearly CSVs of one site -> one contiguous hourly UTC table; refuses gaps and fill values."""
    w = pd.concat([pd.read_csv(io.StringIO(open(data_path("raw", "nasa_power", f"{site}_{y}.csv")).read().split("-END HEADER-\n")[1])) for y in years], ignore_index=True)
    t = pd.to_datetime(dict(year=w.YEAR, month=w.MO, day=w.DY, hour=w.HR))
    assert (t.diff().dropna() == pd.Timedelta("1h")).all() and t.iloc[0] == pd.Timestamp("2001-01-01"), site
    assert (w.drop(columns=["YEAR", "MO", "DY", "HR"]) > -90).all().all(), site       # the file's fill value is -99
    return w


def sites(names: Iterable[str] = ("adelaide", "brisbane", "seville", "almeria", "cordoba", "bilbao", "port_augusta", "longreach"), out: str | None = None) -> dict[str, np.ndarray]:
    """Writes site_wx.npz: hourly tables on the UTC clock, in SITE_COLS order. pvclean.weather.site_year moves them to the price clock."""
    arrs: dict[str, np.ndarray] = {"start_utc": np.array("2001-01-01 00:00:00")}
    for s in names:
        w = read_power(s)
        arrs[s] = w[["ALLSKY_SFC_SW_DWN", "T2M", "WS10M", "PRECTOTCORR"]].values.astype(float)
    np.savez_compressed(out or data_path("site_wx.npz"), **arrs)
    return arrs
