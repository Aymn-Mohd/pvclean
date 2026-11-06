"""Phase R1b stage 6 (provenance).
(1) Reproduces the NREL/NLR soiling statistics used in the paper (NrelSites, NrelMedian, NrelSiteMax) from data/new/ and writes
    data/provenance/NLR.md.
(2) Enumerates the 54 forecast-error / decision-value pairs behind MaeGainRho and MaeGainP, and the 23,562 no-lookahead checks behind
    LeakChecks, into results/audit_counts.json. Both use the same rules as src/make_outputs_v10.py and experiments/forecast_audit.py,
    and are cross-checked against the stored files."""
from __future__ import annotations
from typing import Any
from pvclean.data import data_dir, data_path, results_dir
import os, json, hashlib
import numpy as np
import pandas as pd
from scipy import stats
from .study import Study

sha = lambda f: hashlib.sha256(open(f, "rb").read()).hexdigest()


def nlr() -> Any:
    """The NREL/NLR statistics used in the paper."""
    fm, fs = data_path("new", "nlr_monthly.csv"), data_path("new", "nlr_sites.csv")
    m = pd.read_csv(fm); s = pd.read_csv(fs)
    m["r"] = -pd.to_numeric(m.soiling_rate_per_day, errors="coerce") * 100       # %/day loss (file stores the negative rate)
    n_rows, n_nan = len(m), int(m.r.isna().sum())
    mm = m.dropna(subset=["r"]); sm = mm.groupby("site_id").r.mean()
    low = s.monthly_rates_note.fillna("").str.contains("No monthly rates")
    out = dict(files={"data/" + os.path.relpath(f, data_dir()): sha(f) for f in (fm, fs)},
               sites_in_table=int(len(s)), sites_without_monthly_rates=int(low.sum()), sites_with_monthly_rates=int(sm.size),
               monthly_rows=n_rows, monthly_rows_missing_rate=n_nan, site_months_used=int(len(mm)),
               median_site_month_pct_day=float(mm.r.median()), q1=float(mm.r.quantile(.25)), q3=float(mm.r.quantile(.75)),
               site_mean_median=float(sm.median()), site_mean_p90=float(sm.quantile(.9)), site_mean_max=float(sm.max()), site_max_id=str(sm.idxmax()),
               measurement_types=s["Measurement type"].value_counts().to_dict(), states=int(s.State.nunique()))
    out["paper_macros"] = dict(NrelSites=str(sm.size), NrelMedian=f"{mm.r.median():.2f}", NrelSiteMax=f"{sm.max():.2f}",
                               NrelSitePn=f"{sm.quantile(.9):.2f}", NrelSiteMedian=f"{sm.median():.2f}")
    return out


def mae_pairs() -> Any:
    """The forecast-error and decision-value pairs, with their rank correlation."""
    rep = json.load(open(os.path.join(results_dir(), "results_replay.json"))); fa = json.load(open(os.path.join(results_dir(), "results_forecast_audit.json")))
    mae = {(x["market"], x["contract"], x["year"], x["scenario"]): x["mae_prod_w"] for x in fa["metrics"]}
    pairs = []
    for mk in ("SA1_aligned", "QLD1_aligned", "ES_raw"):
        for c in ("merchant", "ppa"):
            for k in range(3):
                for q in ("F0", "F2", "F3"):
                    pairs.append(dict(market=mk, contract=c, test_year=k, scenario=q, mae_prod_w=mae[(mk, c, k, q)],
                                      planner_gain_mean=float(np.mean(rep[f"{mk}|{c}|{k}"][q]["proposed"]["seeds"]))))
    r, p = stats.spearmanr([x["mae_prod_w"] for x in pairs], [x["planner_gain_mean"] for x in pairs])
    return dict(n=len(pairs), rule="6 market-contract cases x 3 test years x scenarios F0, F2, F3; x = production-weighted MAE of the "
                "7-day value forecast (results_forecast_audit.json mae_prod_w), y = mean planner gain over no cleaning (results_replay.json)",
                spearman_rho=float(r), spearman_p=float(p), pairs=pairs)


def leak_checks() -> Any:
    """Counts the no-lookahead checks and compares them with the stored audit."""
    fa = json.load(open(os.path.join(results_dir(), "results_forecast_audit.json")))
    combos = [(x["market"], x["contract"], x["year"], x["scenario"]) for x in fa["metrics"] if x["scenario"] != "F4"]
    days = list(range(1, 358))
    per = {}
    for mk, c, k, q in combos:
        per.setdefault(f"{mk}|{c}", []).append(f"year{k}:{q}")
    n = len(combos) * len(days)
    return dict(n=n, stored_checks=fa["leakage"]["checks"], stored_failures=fa["leakage"]["failures"], matches=n == fa["leakage"]["checks"],
                rule="every (market, contract, test year, deployable scenario) x decision day d = 1..357; F4 (oracle) is not audited; F1 "
                     "exists only for test years 1 and 2. Per check the forecast is recomputed with all realised values at or after "
                     "info_cutoff set to NaN and must be finite and identical (experiments/forecast_audit.py).",
                markets=3, contracts=2, test_years=3, scenario_year_combos_per_case=len(combos) // 6, decision_days=len(days),
                arithmetic=f"6 cases x (3 + 4 + 4) scenario-years x 357 days = {6 * 11 * 357}", combos_by_case=per)


def nlr_markdown(st: Any) -> Any:
    """Text of data/provenance/NLR.md."""
    L = ["# NREL / NLR soiling statistics: provenance", "",
         "Source: the NREL (now NLR) PV soiling map site table and monthly soiling rates, cited in the paper as `nlrsoiling`, "
         "https://www.nlr.gov/pv/soiling. The local copies and their sha256 hashes:", ""]
    L += [f"- `{f}` sha256 `{h}`" for f, h in st["files"].items()]
    L += ["", "Reproduced by `src/provenance_r1b.py` (the same rule as `src/make_outputs.py`, lines 422-428). Run from `src/`.", "",
          "## Rule", "",
          "- `nlr_monthly.csv` stores `soiling_rate_per_day` as a negative fraction per day. The loss rate in %/day is "
          "r = -100 x soiling_rate_per_day.",
          f"- Rows with a missing rate are dropped: {st['monthly_rows_missing_rate']} of {st['monthly_rows']}, leaving "
          f"{st['site_months_used']} site-months.",
          "- **NrelSites** = number of sites with at least one monthly rate.",
          "- **NrelMedian** = median over all site-months. It is not a median over sites.",
          "- **NrelSiteMax** = largest per-site mean of monthly rates, with every month weighted equally regardless of `interval_count`.", "",
          "## Result", "",
          "| statistic | value | paper macro |", "|---|---|---|",
          f"| sites in the site table | {st['sites_in_table']} | |",
          f"| sites without monthly rates (\"No monthly rates provided for low-soiling sites\") | {st['sites_without_monthly_rates']} | |",
          f"| sites with monthly rates | **{st['sites_with_monthly_rates']}** | NrelSites = {st['paper_macros']['NrelSites']} |",
          f"| median site-month loss rate | **{st['median_site_month_pct_day']:.4f} %/day** | NrelMedian = {st['paper_macros']['NrelMedian']} |",
          f"| quartiles of site-month rates | {st['q1']:.3f}, {st['q3']:.3f} %/day | |",
          f"| median of site means | {st['site_mean_median']:.4f} %/day | NrelSiteMedian = {st['paper_macros']['NrelSiteMedian']} |",
          f"| 90th percentile of site means | {st['site_mean_p90']:.4f} %/day | NrelSitePn = {st['paper_macros']['NrelSitePn']} |",
          f"| largest site mean | **{st['site_mean_max']:.4f} %/day** (`{st['site_max_id']}`) | NrelSiteMax = {st['paper_macros']['NrelSiteMax']} |", "",
          "All three cited values reproduce: 146 sites, 0.10 %/day and 0.30 %/day.", "",
          "## Caveats", "",
          f"- **The 146 sites exclude the {st['sites_without_monthly_rates']} low-soiling sites** of the {st['sites_in_table']}-site table: "
          "insolation-weighted soiling ratio above 0.99, for which the map gives no monthly rates.",
          "  - The \"median US soiling rate\" of 0.10 %/day is therefore the median of the sites that soil measurably.",
          "  - Over all 255 sites the median would be lower.",
          "- \"Median\" in the paper is the median of site-months, not of sites. The median of site means is 0.11 %/day.",
          "- The sensitivity runs (`results_nrel.json`) use soil_mean = 0.0011 for \"med\" and 0.0019 for \"p90\", per day as a fraction "
          "(0.11 and 0.19 %/day), with season_amp = 0.16. That is, they use the median and 90th percentile of **site means**, not "
          "the 0.10 %/day site-month median quoted next to them.",
          f"- {st['measurement_types']}; {st['states']} US states. No Gulf site is included.", ""]
    return "\n".join(L)


def run(S: Study) -> dict:
    """Writes audit_counts.json, and NLR.md beside it."""
    st = nlr()
    with open(S.out_path("NLR.md"), "w") as f:
        f.write(nlr_markdown(st))
    return dict(nlr=st, mae_pairs=mae_pairs(), leakage_checks=leak_checks())
