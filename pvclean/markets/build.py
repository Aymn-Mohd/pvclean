"""Builds hourly real-price arrays with interval-level contract valuation and no wrap-around.

Inputs (raw downloads, not committed; URLs and sha256 in data/provenance/):
  data/raw/aemo/PRICE_AND_DEMAND_<YYYYMM>_<REG>.csv   AEMO 5-min RRP [AUD/MWh], SETTLEMENTDATE = interval end, NEM time (UTC+10)
  data/new/omie.csv                                     OMIE ES day-ahead 2023-2025 (hourly; 15-min from 2025-10-01)
  data/raw/omie/2022/marginalpdbc_202212DD.1            OMIE ES day-ahead Dec 2022 (warm-up only)

For every hour (hour start = floor of interval start) and market:
  mean      mean price [USD/kWh]                    (old-style forecast input; old valuation = f(mean))
  merchant  mean of max(p, 0) over the hour's intervals [USD/kWh]
  ppa_frac  share of the hour's intervals with p >= 0  (PPA value = ppa * ppa_frac)
  neg_share share of the hour's intervals with p < 0
Years are contiguous chronological 365-day slices (29 Feb dropped), never rolled:
  <REG>_aligned  year k = 1 Jul (2022+k) .. 30 Jun (2023+k), k = 0, 1, 2  (A1, A2, A3; sim day 0 = 1 Jul)
  <REG>_raw      year k = calendar 2023+k
  ES_raw         year k = calendar 2023+k
Each year carries 'warm_*' (the 28 days = 672 hours immediately before it, real chronology) and 'ts' (original hour start of
every simulated hour, local market time) for the aligned-to-original mapping. Writes real_prices_v2.npz in the data cache.
data/real_prices.npz, the older hourly file, cannot be rebuilt: its input data/aemo_merged/ no longer exists. See docs/DATA.md."""
from __future__ import annotations
from typing import Any
import glob
import numpy as np
import pandas as pd
from pvclean.config import CONFIG
from pvclean.data import data_path

AUD_USD = CONFIG["aud_usd"]
EUR_USD = CONFIG["eur_usd"]
WARM_DAYS = CONFIG["price_warm_days"]
FIELDS = ("mean", "merchant", "ppa_frac", "neg_share")


def interval_stats(hour_key: Any, p: Any) -> Any:
    """Group interval prices p by hour_key -> DataFrame (index hour) with the four hourly fields and the interval count.
    p is in the market's native unit; conversion to USD/kWh is applied by the caller to mean and merchant only."""
    df = pd.DataFrame(dict(h=hour_key, p=p, pos=np.maximum(p, 0.0), ok=(p >= 0).astype(float), neg=(p < 0).astype(float)))
    g = df.groupby("h", sort=True)
    return pd.DataFrame(dict(mean=g.p.mean(), merchant=g.pos.mean(), ppa_frac=g.ok.mean(), neg_share=g.neg.mean(), n=g.p.size()))


def aemo_hourly(reg: Any) -> Any:
    """Hourly fields of one NEM region, and the raw intervals."""
    files = sorted(glob.glob(data_path("raw", "aemo", f"PRICE_AND_DEMAND_*_{reg}.csv")))
    df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    df = df[df.REGION == reg]
    end = pd.to_datetime(df.SETTLEMENTDATE, format="%Y/%m/%d %H:%M:%S")
    df = df.assign(start=end - pd.Timedelta(minutes=5)).drop_duplicates("start").sort_values("start")
    h = interval_stats(df.start.dt.floor("h").values, df.RRP.values.astype(float))
    h["mean"] *= AUD_USD / 1000.0; h["merchant"] *= AUD_USD / 1000.0
    return h, df


def omie_days() -> Any:
    """Per day: list of native-resolution prices [EUR/MWh] in period order (Dec 2022 + 2023-2025)."""
    days = {}
    for f in sorted(glob.glob(data_path("raw", "omie", "2022", "marginalpdbc_202212*.1"))):
        rows = [l.strip().split(";") for l in open(f, encoding="latin-1") if l[:4].isdigit()]
        rows = [r for r in rows if len(r) >= 6]
        dt = f"{rows[0][0]}-{rows[0][1]}-{rows[0][2]}"
        days[dt] = np.array([float(r[5]) for r in sorted(rows, key=lambda r: int(r[3]))])   # field 6 = ES price
    o = pd.read_csv(data_path("new", "omie.csv"))
    for dt, g in o.groupby("date", sort=True):
        days[dt] = g.sort_values("period").price_ES_eur_mwh.values.astype(float)
    return days


def omie_hourly() -> Any:
    """Hourly fields per day, 24 positions per day. 15-min days (92/96/100 periods) are grouped by 4 consecutive periods;
    DST days (23/25 h) are resampled linearly to 24 positions, as in build_new.py."""
    out = {}
    for dt, p in omie_days().items():
        n = len(p)
        q = 4 if n >= 92 else 1
        hk = np.arange((n // q) * q) // q
        h = interval_stats(hk, p[: (n // q) * q])
        h["mean"] *= EUR_USD / 1000.0; h["merchant"] *= EUR_USD / 1000.0
        if len(h) != 24:
            x = np.linspace(0, 1, len(h)); xi = np.linspace(0, 1, 24)
            h = pd.DataFrame({k: np.interp(xi, x, h[k].values) for k in FIELDS}).assign(n=0)
        out[dt] = h
    return out


def drop_feb29(idx: Any) -> Any:
    """The index without 29 February."""
    return idx[~((idx.month == 2) & (idx.day == 29))]


def slice_years(h: Any, starts: Any, label: Any) -> Any:
    """Contiguous 365-day years from each start date, warm-up = the 28 days before; h indexed by hour start."""
    res = {k: [] for k in FIELDS}; res.update({"warm_" + k: [] for k in FIELDS}); res["ts"] = []
    for s in starts:
        s = pd.Timestamp(s)
        hrs = drop_feb29(pd.date_range(s, s + pd.Timedelta(days=366), freq="1h", inclusive="left"))[:8760]
        warm = drop_feb29(pd.date_range(s - pd.Timedelta(days=WARM_DAYS + 1), s, freq="1h", inclusive="left"))[-WARM_DAYS * 24:]
        assert len(hrs) == 8760 and len(warm) == WARM_DAYS * 24, (label, s)
        for k in FIELDS:
            a = h[k].reindex(hrs).values; w = h[k].reindex(warm).values
            assert np.isfinite(a).all() and np.isfinite(w).all(), (label, s, k, int(np.isnan(a).sum()), int(np.isnan(w).sum()))
            res[k].append(a); res["warm_" + k].append(w)
        res["ts"].append(hrs.values.astype("datetime64[s]"))
    return {k: np.array(v) for k, v in res.items()}


def build(out: Any = None) -> Any:
    """Writes the price arrays; returns them with a summary of the inputs."""
    out = out or data_path("real_prices_v2.npz")
    arrs, meta = {}, {}
    for reg in ("SA1", "QLD1"):
        h, raw = aemo_hourly(reg)
        meta[reg] = dict(intervals=int(len(raw)), first=str(raw.start.min()), last=str(raw.start.max()),
                         hours_not_12=int((h.n != 12).sum()))
        for name, starts in ((f"{reg}_aligned", ["2022-07-01", "2023-07-01", "2024-07-01"]),
                             (f"{reg}_raw", ["2023-01-01", "2024-01-01", "2025-01-01"])):
            for k, v in slice_years(h, starts, name).items():
                arrs[f"{name}|{k}"] = v
    od = omie_hourly()
    idx, rows = [], []
    for dt in sorted(od):
        idx.extend(pd.date_range(dt, periods=24, freq="1h")); rows.append(od[dt][list(FIELDS)].values)
    h = pd.DataFrame(np.concatenate(rows), index=pd.DatetimeIndex(idx), columns=list(FIELDS))
    meta["ES"] = dict(days=len(od), first=min(od), last=max(od))
    for k, v in slice_years(h, ["2023-01-01", "2024-01-01", "2025-01-01"], "ES_raw").items():
        arrs[f"ES_raw|{k}"] = v
    np.savez(out, **arrs)
    return arrs, meta


def old_style(mean: Any, ppa: Any = 1.0) -> Any:
    """Hourly-mean valuation (v9/v10): merchant = max(mean, 0), PPA paid iff mean >= 0."""
    return np.maximum(mean, 0.0), np.where(mean >= 0, 1.0, 0.0)
