"""Matched sites: the R1 replay with the plant placed in each price market, on real local weather of the same calendar years as the prices. Also the wider kappa grid (POST HOC) and the
gauge rain table."""
from __future__ import annotations
import json
import os
import time
from typing import Any
import numpy as np
from pvclean import model
from pvclean.data import repo_root
from pvclean.sites import site_config
from pvclean.stats import decomp, paired, tally_rule
from .chrono import CONTRACTS, FOLDS, MODES, run_fold
from .study import Study

CAL = (2023, 2024, 2025)       # calendar year of price index 0, 1, 2
MARKET_SITES = {"SA1_raw": "adelaide", "QLD1_raw": "brisbane", "ES_raw": "seville"}
MARKETS = list(MARKET_SITES)
SITES = {mk: site_config(s) for mk, s in MARKET_SITES.items()}
SOIL = {"soil0.30": 0.0030, "soil0.11": 0.0011}
FOLD_NAMES = ("Y2", "Y3")


def site_over(mk: str, test_year: int, soil: float = 0.0030) -> dict[str, Any]:
    """Config of one market and fold; the climatology stops at the year before the test year."""
    return dict(SITES[mk], wx_site_years=CAL, clim_years=tuple(range(2001, test_year)), soil_mean=soil)


def fold_test_year(fold: str) -> int:
    """Calendar year tested by a fold."""
    return CAL[FOLDS[fold][1][0]]


def decomps(rec: dict[str, Any]) -> dict[str, Any]:
    """The two decompositions of a case."""
    t = rec["test"]["F2"]; bb = rec["best_baseline"]
    return {"planner-ft": decomp(t["proposed"], t["ft"], rec["vref"]), "planner-bestbase": decomp(t["proposed"], t[bb], rec["vref"])}


def run_case(rn: Any, soil: str, mk: str, c: str, fold: str, modes: dict[str, str] = MODES) -> dict[str, Any]:
    """One case-year at one soiling level."""
    rec = run_fold(rn, mk, c, fold, extra=site_over(mk, fold_test_year(fold), SOIL[soil]), modes=modes)
    rec["label"] = "MAIN-R3" if soil == "soil0.30" else "SENSITIVITY"
    rec["test_year"] = fold_test_year(fold); rec["site"] = SITES[mk]["wx_site"]; rec["soil_mean"] = SOIL[soil]
    rec["decomp"] = decomps(rec)
    return rec


def verdict(r3: dict[str, Any], soil: str) -> dict[str, Any]:
    """The H-R3 rule at one soiling level."""
    return tally_rule(r3[f"{soil}|{mk}|{c}|{f}"]["cmp"]["planner-ft|F2"] for mk in MARKETS for c in CONTRACTS for f in FOLD_NAMES)


def r3(S: Study) -> dict[str, Any]:
    """The R3 replay (keys r3 and r3_meta of results_matched.json)."""
    t0 = time.time(); r: dict[str, Any] = {}
    with S.runner_pool() as rn:
        for soil in S.params["soil"]:
            for mk in MARKETS:
                for c in CONTRACTS:
                    for fold in FOLD_NAMES:
                        r[f"{soil}|{mk}|{c}|{fold}"] = run_case(rn, soil, mk, c, fold)
    meta = dict(train_seeds=S.protocol.train, test_seeds=S.protocol.test, modes=MODES, workers=S.protocol.workers, runtime_s_last=time.time() - t0, sites=SITES, calendar=CAL, soil=SOIL,
                verdict_H_R3=verdict(r, "soil0.30"), sensitivity_soil011=verdict(r, "soil0.11") if "soil0.11" in S.params["soil"] else None)
    return dict(r3=r, r3_meta=meta)


def site_report(mk: str) -> dict[str, Any]:
    """Annual DC yield and rain days of one market's site, every year 2002-2025, the test years, and two chain checks."""
    base = model.merged(SITES[mk])
    yrs = {}
    for y in range(2002, 2026):
        a = model.site_year(y, base)
        yrs[y] = dict(dc_kwh_kwp=float(a["pdc"].sum()), rain_mm=float(a["rain"].sum()), rain_days_1mm=int((a["rain"] >= 1).sum()), rain_days_5mm=int((a["rain"] >= 5).sum()))
    wind3 = {y: float(model.site_year(y, dict(base, wx_wind=3.0))["pdc"].sum()) for y in CAL}
    flip = {y: float(model.site_year(y, dict(base, azimuth=(base["azimuth"] + 180.0) % 360))["pdc"].sum()) for y in CAL}
    return dict(site=base["wx_site"], lat=base["lat"], lon=base["lon"], azimuth=base["azimuth"], years=yrs, wind_fixed_3ms_dc=wind3, opposite_azimuth_dc=flip,
                mean_2002_2025=dict(dc_kwh_kwp=float(np.mean([v["dc_kwh_kwp"] for v in yrs.values()])), rain_days_1mm=float(np.mean([v["rain_days_1mm"] for v in yrs.values()])),
                                    rain_days_5mm=float(np.mean([v["rain_days_5mm"] for v in yrs.values()]))))


def site_weather(S: Study) -> dict[str, Any]:
    """Site yields and rain days (r3_site_weather.json)."""
    return {mk: site_report(mk) for mk in MARKETS}


# POST HOC after R3, not pre-registered. The R3 verdict is unchanged.
UNCHANGED = ("fixed", "threshold", "econ", "ft")


def sign(x: float) -> str:
    """The sign of a number, as text."""
    return "+" if x > 0 else "-" if x < 0 else "0"


def check_against_r3(rec: dict[str, Any], old: dict[str, Any]) -> bool:
    """Stops the run if anything other than the planner moved. Returns True if the planner kept its R3 parameters."""
    t, o = rec["test"]["F2"], old["test"]["F2"]
    assert rec["best_baseline"] == old["best_baseline"], "selected baseline moved"
    assert np.array_equal(rec["vref"], old["vref"]), "vref moved"
    assert np.array_equal(t["none"]["net"], o["none"]["net"]), "no-cleaning moved"
    for p in UNCHANGED:
        assert rec["tuned"]["F2"][p] == old["tuned"]["F2"][p], f"{p} tuning moved"
        assert np.array_equal(t[p]["net"], o[p]["net"]), f"{p} test net moved"
    a, b = rec["tuned"]["F2"]["proposed"], old["tuned"]["F2"]["proposed"]
    assert a["train_mean"] >= b["train_mean"], "training mean fell on a wider grid"
    same = a["params"] == b["params"]
    if same:
        assert np.array_equal(t["proposed"]["net"], o["proposed"]["net"]), "planner moved with the same parameters"
    return same


def kappa_row(rec: dict[str, Any], old: dict[str, Any]) -> dict[str, Any]:
    """What the report needs from one case, next to R3's stored values."""
    t, o = rec["test"]["F2"], old["test"]["F2"]; bb = rec["best_baseline"]
    now = dict(ft=rec["cmp"]["planner-ft|F2"], bestbase=rec["cmp"]["planner-bestbase|F2"])
    was = dict(ft=old["cmp"]["planner-ft|F2"], bestbase=old["cmp"]["planner-bestbase|F2"])
    return dict(best_baseline=bb, planner_ft=now["ft"], planner_bestbase=now["bestbase"], r3_planner_ft=was["ft"], r3_planner_bestbase=was["bestbase"],
                params=rec["tuned"]["F2"]["proposed"]["params"], r3_params=old["tuned"]["F2"]["proposed"]["params"],
                train_mean=rec["tuned"]["F2"]["proposed"]["train_mean"], r3_train_mean=old["tuned"]["F2"]["proposed"]["train_mean"],
                row_cleanings=dict(planner=float(np.mean(t["proposed"]["n_clean"])), ft=float(np.mean(t["ft"]["n_clean"])), r3_planner=float(np.mean(o["proposed"]["n_clean"])),
                                   planner_minus_ft=paired(t["proposed"]["n_clean"], t["ft"]["n_clean"])),
                planner_minus_r3_planner=paired(t["proposed"]["net"], o["proposed"]["net"]), planner_minus_none=paired(t["proposed"]["net"], t["none"]["net"]),
                ft_minus_none=paired(t["ft"]["net"], t["none"]["net"]), ties_with_ft=int(np.sum(np.abs(np.subtract(t["proposed"]["net"], t["ft"]["net"])) < 1e-6)),
                sign_ft=sign(now["ft"]["mean"]), r3_sign_ft=sign(was["ft"]["mean"]), sign_bestbase=sign(now["bestbase"]["mean"]), r3_sign_bestbase=sign(was["bestbase"]["mean"]))


def kappa_tally(rows: dict[str, Any], top: float) -> dict[str, Any]:
    """Counts over the 12 case-years. Descriptive: not a new verdict."""
    m = [r["planner_ft"] for r in rows.values()]
    return dict(n=len(m), mean_pos=sum(x["mean"] > 0 for x in m), mean_nonpos=sum(x["mean"] <= 0 for x in m), ci_wholly_above=sum(x["lo"] > 0 for x in m), ci_wholly_below=sum(x["hi"] < 0 for x in m),
                sign_changes_ft=sum(r["sign_ft"] != r["r3_sign_ft"] for r in rows.values()), sign_changes_bestbase=sum(r["sign_bestbase"] != r["r3_sign_bestbase"] for r in rows.values()),
                planner_more_rows_than_ft=sum(r["row_cleanings"]["planner"] > r["row_cleanings"]["ft"] for r in rows.values()), kappa_at_grid_top=sum(r["params"]["kappa"] == top for r in rows.values()))


def kappa(S: Study) -> dict[str, Any]:
    """The 12 R3 case-years under F2 with the wider kappa grid of the study's protocol (results_matched_posthoc_kappa.json)."""
    soil = S.params["soil"]; stored = S.stored("results_matched.json")["r3"]; kgrid = S.params["kappa_grid"]
    t0 = time.time(); rows: dict[str, Any] = {}; cases: dict[str, Any] = {}
    with S.runner_pool() as rn:
        for mk in MARKETS:
            for c in CONTRACTS:
                for f in FOLD_NAMES:
                    k = f"{mk}|{c}|{f}"; old = stored[f"{soil}|{k}"]
                    rec = run_case(rn, soil, mk, c, f, modes={"F2": "roll"}); rec["label"] = "POST HOC"
                    same = check_against_r3(rec, old)
                    rows[k] = dict(kappa_row(rec, old), planner_params_same_as_r3=same); cases[k] = rec
    meta = dict(label="POST HOC", note="Not pre-registered; the R3 verdict is unchanged.", soil=soil, forecast="F2", kappa_grid=kgrid, beta_grid=S.params["beta_grid"], r3_kappa_grid=S.params["r3_kappa_grid"],
                train_seeds=S.protocol.train, test_seeds=S.protocol.test, workers=S.protocol.workers, runtime_s_last=time.time() - t0, tally=kappa_tally(rows, kgrid[-1]))
    return dict(_meta=meta, rows=rows, cases=cases)


def longest_dry_run(rain: np.ndarray, mm: float = 5.0) -> int:
    """Longest run of days without a day >= mm, counting the stretches before the first and after the last such day."""
    big = np.flatnonzero(np.asarray(rain) >= mm)
    return int((np.diff(np.r_[-1, big, len(rain)]) - 1).max())


def rain_stats(rain: np.ndarray) -> dict[str, Any]:
    """Annual total, rain days and the longest dry run."""
    return dict(total_mm=float(np.sum(rain)), days_5mm=int((rain >= 5).sum()), days_1mm=int((rain >= 1).sum()), longest_run_without_5mm=longest_dry_run(rain))


def gauge_rain(S: Study) -> dict[str, Any]:
    """R3b: the NASA POWER side of the rain table. No gauge data could be obtained, so the 25% rule is "not evaluable", which is not "not triggered" (results_r3b_rain.json)."""
    prov = json.load(open(os.path.join(repo_root(), "data", "provenance", "r3b_gauges.json")))
    assert not prov["gauge_files"], "gauge data exists: this runner does not read it yet"
    att = {a["site"]: a for a in prov["attempts"]}; sites = {}
    for mk in MARKETS:
        site = SITES[mk]["wx_site"]; a = att[site]
        sites[site] = dict(market=mk, gauge_station=a["station"], gauge_source=a["source"], gauge_status=a["outcome"], gauge_http_status=a["http_status"],
                           years={y: dict(nasa=rain_stats(model.site_year(y, model.merged(SITES[mk]))["rain"]), gauge=None) for y in CAL}, rule_25pct="not evaluable", rerun=None)
    return dict(_meta=dict(label="ANALYSIS / SENSITIVITY", note="The R3 verdict is unchanged. No gauge data: the comparison and the 25% rule could not be evaluated, and no site was rerun.",
                           test_years=S.params["test_years"], gauge_files=0, sites_triggered=None, sites_rerun=[]), sites=sites)
