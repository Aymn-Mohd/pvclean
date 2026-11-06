"""results/macro_inputs.json: the few numbers the paper macros take from market, weather and soiling data. They are stored so that macros can be rebuilt without the data."""
from __future__ import annotations
from typing import Any
import numpy as np
import pandas as pd
from pvclean import model
from pvclean.data import data_path


def compute(cfg_stored: dict[str, Any]) -> dict[str, Any]:
    """Recomputes the numbers from the data cache. cfg_stored is the config stored in results.json."""
    cfg = dict(model.CONFIG, **cfg_stored)
    npz = np.load(data_path("real_prices.npz"))
    es = npz["ES_raw"]
    out: dict[str, Any] = {"es": dict(neg=float((es < 0).mean()), neg_y=[float((es[i] < 0).mean()) for i in range(3)], zero=float((es == 0).mean()),
                                      jump=float(es[0].mean() / es[1:].mean()), mean=float(es.mean()))}
    w_ = np.mean([model.weather(s_, cfg)["pdc"] for s_ in range(1000, 1005)], axis=0)
    day_ = w_ > 0.05 * w_.max()
    for mk in ("SA1", "QLD1"):
        arr = npz[f"{mk}_aligned"]
        out[mk] = dict(neg=float((arr < 0).mean()), neg_day=float((arr[:, day_] < 0).mean()), neg_y=[float((arr[i] < 0).mean()) for i in range(3)])
    wxz = np.load(data_path("dubai_wx.npz"))
    yrs_ = [str(y) for y in range(2002, 2026)]
    cfg_r = dict(model.CONFIG); cfg_r["wx_years"] = tuple(range(2002, 2026))
    out["wx"] = dict(real_yield=float(np.mean([model.weather(s_, cfg_r)["pdc"].sum() for s_ in range(24)])),
                     rain_days_1mm=[int((wxz[y][:, 3].reshape(365, 24).sum(1) >= 1).sum()) for y in yrs_], rain_days_5mm=[int((wxz[y][:, 3].reshape(365, 24).sum(1) >= 5).sum()) for y in yrs_])
    m = pd.read_csv(data_path("new", "nlr_monthly.csv"))
    m["r"] = -pd.to_numeric(m.soiling_rate_per_day, errors="coerce") * 100
    m = m.dropna(subset=["r"])
    sm = m.groupby("site_id").r.mean()
    m["rel"] = m.r / m.groupby("site_id").r.transform("mean")
    prof = m.groupby("month").rel.mean()
    out["nrel"] = dict(sites=int(sm.size), site_months=int(len(m)), median=float(m.r.median()), q1=float(m.r.quantile(.25)), q3=float(m.r.quantile(.75)), site_median=float(sm.median()),
                       site_p90=float(sm.quantile(.9)), site_max=float(sm.max()), prof_max=float(prof.max()), prof_min=float(prof.min()), prof_peak=str(prof.idxmax()))
    return out
