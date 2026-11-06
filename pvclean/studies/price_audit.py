"""Phase R1 price audit: hourly-mean (v9/v10) versus interval-level valuation on the same contiguous R1 years.
Per market and year: uncleaned-plant revenue (merchant and PPA, mean over the 50 test seeds' weather), PPA zero-payment hours
(old: hours with mean price < 0; new: sum over hours of the unpaid interval share, plus hours with any negative interval),
negative-hour share (old) and negative-interval share (new). Writes price_audit.json."""
from __future__ import annotations
from typing import Any
from pvclean import model
from pvclean.data import data_path
from pvclean.markets.build import old_style
import os
import tempfile
import numpy as np
from .study import Study

MARKETS = {"SA1_aligned": ["A1 2022-23", "A2 2023-24", "A3 2024-25"], "QLD1_aligned": ["A1 2022-23", "A2 2023-24", "A3 2024-25"],
           "ES_raw": ["2023", "2024", "2025"], "SA1_raw": ["2023", "2024", "2025"], "QLD1_raw": ["2023", "2024", "2025"]}


def uncleaned_revenue(contract: Any, mk: Any, k: Any, npz: Any, test: Any) -> Any:
    """Mean revenue of the uncleaned plant over the test seeds."""
    cfg = dict(model.CONFIG, real_value=mk, real_years=(k,), value_npz=npz)
    return float(np.mean([model.simulate("none", {}, contract, s, cfg=cfg)["revenue"] for s in test]))


def audit(test: Any) -> Any:
    """Hourly-mean against interval-level valuation, per market and year."""
    z = dict(np.load(data_path("real_prices_v2.npz")))
    old = {}
    for mk in MARKETS:
        m, f = old_style(z[f"{mk}|mean"])
        old[f"{mk}|merchant"] = m; old[f"{mk}|ppa_frac"] = f
    tmp = tempfile.mktemp(suffix=".npz"); np.savez(tmp, **old)
    new = data_path("real_prices_v2.npz")
    out = []
    for mk, labels in MARKETS.items():
        for k, lab in enumerate(labels):
            mean = z[f"{mk}|mean"][k]; frac = z[f"{mk}|ppa_frac"][k]; neg = z[f"{mk}|neg_share"][k]
            row = dict(market=mk, year=k, label=lab,
                       merchant_rev_uncleaned_old=uncleaned_revenue("merchant", mk, k, tmp, test),
                       merchant_rev_uncleaned_new=uncleaned_revenue("merchant", mk, k, new, test),
                       ppa_rev_uncleaned_old=uncleaned_revenue("ppa", mk, k, tmp, test),
                       ppa_rev_uncleaned_new=uncleaned_revenue("ppa", mk, k, new, test),
                       ppa_zero_hours_old=int((mean < 0).sum()),
                       ppa_unpaid_hours_new=float((1 - frac).sum()),
                       hours_any_negative_interval=int((neg > 0).sum()),
                       neg_hour_share_old=float((mean < 0).mean()),
                       neg_interval_share_new=float(neg.mean()),
                       mean_price_usd_kwh=float(mean.mean()),
                       merchant_value_mean_old=float(np.maximum(mean, 0).mean()),
                       merchant_value_mean_new=float(z[f"{mk}|merchant"][k].mean()))
            for c in ("merchant", "ppa"):
                row[f"{c}_rev_change_pct"] = 100 * (row[f"{c}_rev_uncleaned_new"] / row[f"{c}_rev_uncleaned_old"] - 1)
            out.append(row)
    os.remove(tmp)
    return dict(note="old = hourly-mean valuation (v9/v10 rule) applied to the same contiguous R1 years; new = interval-level", rows=out)


def run(S: Study) -> dict:
    """Writes price_audit.json."""
    return audit(S.protocol.test)
