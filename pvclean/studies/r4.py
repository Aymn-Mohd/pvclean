"""Phase R4: new sites in the three price markets, to test whether the longest dry spell, measured from rain alone, predicts the sign of planner minus FT. Every job reuses the R3 replay;
only the site, and for the checks one named setting, differ. Pre-registration: docs/records/decisions.md, "Phase R4"."""
from __future__ import annotations
import time
from typing import Any
import numpy as np
from pvclean import model
from pvclean.sites import load_site, site_config
from pvclean.stats import paired
from .chrono import CONTRACTS, run_fold
from .matched import CAL, FOLD_NAMES, SOIL, decomps, fold_test_year, rain_stats
from .runner import Runner, record_job
from .study import Study

R3_SITES = ("adelaide", "brisbane", "seville")
NEW_SITES = ("almeria", "cordoba", "bilbao", "port_augusta", "longreach")
F2_ONLY = {"F2": "roll"}
POLS = ("fixed", "threshold", "econ", "ft", "proposed")


def market_of(site: str) -> str:
    """The price series of a site."""
    return load_site(site)["market"]


def site_over(site: str, test_year: int, soil: float = 0.0030) -> dict[str, Any]:
    """Config of one site and fold, as matched.site_over: the climatology stops at the year before the test year."""
    return dict(site_config(site), wx_site_years=CAL, clim_years=tuple(range(2001, test_year)), soil_mean=soil)


def cases(sites: tuple[str, ...]) -> list[tuple[str, str, str]]:
    """Site x contract x fold."""
    return [(s, c, f) for s in sites for c in CONTRACTS for f in FOLD_NAMES]


def sites_of(S: Study) -> tuple[str, ...]:
    """The sites of a study: params `sites` is `new`, `all`, or a list."""
    v = S.params.get("sites", "new")
    return NEW_SITES if v == "new" else R3_SITES + NEW_SITES if v == "all" else tuple(v)


def run_case(rn: Runner, site: str, c: str, fold: str, label: str, soil: float = 0.0030, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    """One case-year under F2, with the schema of a results_matched.json record."""
    y = fold_test_year(fold)
    rec = run_fold(rn, market_of(site), c, fold, extra=dict(site_over(site, y, soil), **(extra or {})), modes=F2_ONLY)
    rec["label"] = label; rec["test_year"] = y; rec["site"] = site; rec["soil_mean"] = soil
    rec["decomp"] = decomps(rec)
    return rec


def row(rec: dict[str, Any]) -> dict[str, Any]:
    """Compact record of one case: comparisons, parameters, value of cleaning, rows cleaned and the planner minus FT split."""
    t = rec["test"]["F2"]; none = np.array(t["none"]["net"])
    return dict(site=rec["site"], market=rec["market"], contract=rec["contract"], test_year=rec["test_year"], planner_ft=rec["cmp"]["planner-ft|F2"], planner_bestbase=rec["cmp"]["planner-bestbase|F2"],
                best_baseline=rec["best_baseline"], params={p: rec["tuned"]["F2"][p]["params"] for p in POLS}, none_net=float(none.mean()),
                voc={p: float(np.mean(np.array(t[p]["net"]) - none)) for p in POLS}, row_cleanings={p: float(np.mean(t[p]["n_clean"])) for p in POLS},
                planner_minus_none=paired(t["proposed"]["net"], none), ft_minus_none=paired(t["ft"]["net"], none),
                ties_with_ft=int(np.sum(np.abs(np.subtract(t["proposed"]["net"], t["ft"]["net"])) < 1e-6)),
                quantity=rec["decomp"]["planner-ft"]["quantity"], timing=rec["decomp"]["planner-ft"]["timing"], d_row_cleanings=rec["decomp"]["planner-ft"]["d_row_cleanings"])


def tally(rows: dict[str, Any]) -> dict[str, Any]:
    """Counts of planner minus FT over the case-years."""
    m = [r["planner_ft"] for r in rows.values()]
    return dict(n=len(m), mean_pos=sum(x["mean"] > 0 for x in m), mean_nonpos=sum(x["mean"] <= 0 for x in m), ci_wholly_above=sum(x["lo"] > 0 for x in m), ci_wholly_below=sum(x["hi"] < 0 for x in m))


def replay(rn: Runner, sites: tuple[str, ...], label: str, soil: float = 0.0030, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    """All case-years of some sites, as compact rows with their tally."""
    rows = {f"{s}|{c}|{f}": row(run_case(rn, s, c, f, label, soil, extra)) for s, c, f in cases(sites)}
    return dict(rows=rows, tally=tally(rows))


def soiling_loss(rn: Runner, site: str, y: int) -> float:
    """No-cleaning energy loss of one site-year against a dust-free run, in percent, over the test seeds: the method of r3_checks.part_soil."""
    yi = CAL.index(y)
    base = dict(site_over(site, y), real_value=market_of(site), real_years=(yi,), fc_mode="roll", roll_min_hist=1)
    jobs = [("none", {}, "merchant", s, "site", 0.01, 1.0, o) for o in (base, dict(base, soil_mean=0.0, storm_rate=0.0)) for s in rn.test]
    r = rn.map(record_job, jobs); n = len(rn.test)
    dirty = np.mean([x["energy_kwh"] for x in r[:n]]); clean = np.mean([x["energy_kwh"] for x in r[n:]])
    return float(100 * (1 - dirty / clean))


def rain(S: Study) -> dict[str, Any]:
    """Rain statistics of the new sites, from rain alone (r4_rain.json). The same definition and code as results_r3b_rain.json."""
    out = {}
    for s in sites_of(S):
        base = model.merged(site_config(s))
        out[s] = dict(market=market_of(s), lat=base["lat"], lon=base["lon"], years={y: rain_stats(model.site_year(y, base)["rain"]) for y in S.params["years"]})
    return dict(_meta=dict(label="INPUT", note="Local-day NASA POWER rain on the price clock, 365 days, 29 Feb dropped. Longest run: longest stretch without a day >= 5 mm, including the stretches before the first and after the last such day."),
                sites=out)


def _meta(S: Study, t0: float, label: str, **kw: Any) -> dict[str, Any]:
    """Run facts of a job."""
    return dict(label=label, train_seeds=S.protocol.train, test_seeds=S.protocol.test, forecast="F2", workers=S.protocol.workers, runtime_s_last=time.time() - t0, calendar=CAL, **kw)


def sites_job(S: Study) -> dict[str, Any]:
    """The prediction test: full records, with the schema of results_matched.json, plus the soiling loss of each site-year (results_r4_sites.json)."""
    t0 = time.time(); sites = sites_of(S); r: dict[str, Any] = {}
    with S.runner_pool() as rn:
        for s, c, f in cases(sites):
            r[f"soil0.30|{s}|{c}|{f}"] = run_case(rn, s, c, f, "MAIN-R4")
        loss = {f"{s}|{fold_test_year(f)}": soiling_loss(rn, s, fold_test_year(f)) for s in sites for f in FOLD_NAMES}
    return dict(r4=r, r4_meta=_meta(S, t0, "MAIN-R4", sites={s: dict(site_config(s), market=market_of(s)) for s in sites}, modes=F2_ONLY, soil=dict(SOIL), soiling_loss_pct=loss))


def kappa_job(S: Study) -> dict[str, Any]:
    """POST HOC: the wider kappa grid of the study's protocol (results_r4_kappa.json). Nothing but the planner may move against results_r4_sites.json."""
    t0 = time.time(); sites = sites_of(S); stored = S.stored("results_r4_sites.json")["r4"]; rows: dict[str, Any] = {}; moved = 0
    with S.runner_pool() as rn:
        for s, c, f in cases(sites):
            rec = run_case(rn, s, c, f, "POST HOC"); old = stored.get(f"soil0.30|{s}|{c}|{f}")
            rows[f"{s}|{c}|{f}"] = row(rec)
            if old is not None:
                t, o = rec["test"]["F2"], old["test"]["F2"]
                assert rec["best_baseline"] == old["best_baseline"] and np.array_equal(t["none"]["net"], o["none"]["net"]), "a baseline moved"
                for p in ("fixed", "threshold", "econ", "ft"):
                    assert rec["tuned"]["F2"][p] == old["tuned"]["F2"][p] and np.array_equal(t[p]["net"], o[p]["net"]), f"{p} moved"
                assert rec["tuned"]["F2"]["proposed"]["train_mean"] >= old["tuned"]["F2"]["proposed"]["train_mean"], "training mean fell on a wider grid"
                moved += rec["tuned"]["F2"]["proposed"]["params"] != old["tuned"]["F2"]["proposed"]["params"]
    kg = S.params["kappa_grid"]
    return dict(_meta=_meta(S, t0, "POST HOC", kappa_grid=kg, planner_params_moved=int(moved), kappa_at_grid_top=sum(r["params"]["proposed"]["kappa"] == kg[-1] for r in rows.values())), rows=rows, tally=tally(rows))


def shift_job(S: Study) -> dict[str, Any]:
    """POST HOC: dust and storm seasons moved by half a year (results_r4_shift.json). The R3 sites must match the stored R3 check."""
    t0 = time.time(); d = S.params["shift_days"]
    with S.runner_pool() as rn:
        res = replay(rn, sites_of(S), "POST HOC", extra=dict(season_shift=d))
    return dict(_meta=_meta(S, t0, "POST HOC", shift_days=d), **res)


def lowsoil_job(S: Study) -> dict[str, Any]:
    """POST HOC: 0.11 %/day; only soil_mean changes, as in R3 (results_r4_lowsoil.json)."""
    t0 = time.time(); soil = S.params["soil_mean"]
    with S.runner_pool() as rn:
        res = replay(rn, sites_of(S), "POST HOC", soil=soil)
    return dict(_meta=_meta(S, t0, "POST HOC", soil_mean=soil), **res)


def cost_job(S: Study) -> dict[str, Any]:
    """SENSITIVITY: c_row and c_mission scaled together, every policy retuned (results_r4_cost.json)."""
    t0 = time.time(); arms: dict[str, Any] = {}; c = model.CONFIG
    with S.runner_pool() as rn:
        for m in S.params["multipliers"]:
            arms[f"x{m}"] = dict(multiplier=m, **replay(rn, sites_of(S), "SENSITIVITY", extra=dict(c_row=c["c_row"] * m, c_mission=c["c_mission"] * m)))
    return dict(_meta=_meta(S, t0, "SENSITIVITY", multipliers=S.params["multipliers"], c_row=c["c_row"], c_mission=c["c_mission"]), arms=arms)


def seeds_job(S: Study) -> dict[str, Any]:
    """SENSITIVITY: tuning repeated on other train seeds, test seeds unchanged (results_r4_seeds.json)."""
    t0 = time.time(); sets = S.params["retune"]
    with S.runner_pool() as rn:
        out = {name: replay(rn.with_(train=seeds), sites_of(S), "SENSITIVITY") for name, seeds in sets.items()}
    return dict(_meta=_meta(S, t0, "SENSITIVITY", retune=sets), sets=out)
