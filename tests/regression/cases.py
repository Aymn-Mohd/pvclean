"""Small fixed-seed runs, one per study type. Each case returns plain data; canon() turns it into exact text for the golden files."""
import hashlib, json, os
from multiprocessing import Pool
import numpy as np
import api
from api import sim, exact, optimisation, forecasting, checks, chrono as chrono_study, mr, rs, belief_world

SUMMARY = ("net", "revenue", "energy_kwh", "cost_clean", "cost_mission", "cost_insp", "n_clean", "n_missions")
POLICIES = [("none", {}), ("fixed", {"T": 14}), ("threshold", {"theta": 0.05}), ("econ", {"b": 4}), ("ft", {"Hb": 14, "b": 2, "antic": 1}),
            ("proposed", {"beta": 0.5, "kappa": 0.5}), ("proposed_noval", {"beta": 0.5, "kappa": 1}), ("proposed_nobatch", {"b": 4})]
SMALL = dict(n_rows=6, night_min=100.0, d0=120, d1=180)
TINY_GRID = {"fixed": [{"T": 14}, {"T": 28}], "threshold": [{"theta": 0.05}, {"theta": 0.1}], "econ": [{"b": 2}, {"b": 8}],
             "ft": [{"Hb": 7, "b": 2, "antic": 0}, {"Hb": 14, "b": 4, "antic": 1}], "proposed": [{"beta": 0, "kappa": 0.5}, {"beta": 0.5, "kappa": 2}]}


def digest(a):
    a = np.ascontiguousarray(a)
    return dict(shape=list(a.shape), dtype=str(a.dtype), sha256=hashlib.sha256(a.tobytes()).hexdigest())


def canon(x):
    """Plain JSON data: floats keep their exact repr; arrays become a shape and a hash of their bytes."""
    if isinstance(x, dict):
        return {str(k): canon(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [canon(v) for v in x]
    if isinstance(x, np.ndarray):
        return digest(x)
    if isinstance(x, np.bool_):
        return bool(x)
    if isinstance(x, np.integer):
        return int(x)
    if isinstance(x, np.floating):
        return float(x)
    return x


def text(x):
    return json.dumps(canon(x), indent=1, sort_keys=True) + "\n"


def digest_text(x):
    """Hash of a long log, so that a golden file stays small but still detects any change."""
    return hashlib.sha256(text(x).encode()).hexdigest()


def run_one(pol, par, contract, seed, cfg, inp, **kw):
    c, v, p = inp
    r = sim.simulate(pol, par, contract, seed, cfg=cfg, clim=c, vexp=v, pbar=p, **kw)
    out = {k: r[k] for k in SUMMARY}
    out["sched"] = r["sched"]
    return out


def generated():
    """Generated market: inputs, every policy and contract, information regimes, every simulator option, tuning and evaluation."""
    base = dict(sim.CONFIG); res = {}
    res["series"] = {str(s): dict(weather=sim.weather(s, base), spot=sim.spot_prices(s, base), dust=sim.dust(s, base), fc=sim.rain_forecast(sim.weather(s, base)["rain"], s, base),
                                  up=sim.robot_up(s, dict(base, availability=0.9))) for s in (0, 1)}
    res["exposure"] = {str(h): sim.exposure(base, hetero=h) for h in (0.0, 1.0, 2.0)}
    for c in ("fixed", "merchant", "ppa", "capped"):
        inp = sim.planner_inputs(c, base)
        res[f"inputs|{c}"] = inp
        for pol, par in POLICIES:
            for s in (0, 1, 2):
                res[f"{c}|{pol}|{s}"] = run_one(pol, par, c, s, base, inp)
    inp = sim.planner_inputs("merchant", base)
    for pol, par in POLICIES[1:6]:
        for info, sig in (("mobile", 0.01), ("perfect", 0.0)):
            res[f"info|{info}|{pol}"] = run_one(pol, par, "merchant", 3, base, inp, info=info, sigma=sig, hetero=1.5)
    variants = {"noaccess": {"blackouts": ()}, "bias": {"station_bias": 0.25}, "eff": {"clean_residual": 0.02}, "rain2": {"rain_scale": 2.0}, "price2": {"price_depress_scale": 2.0},
                "shift": {"season_shift": 182}, "soil": {"soil_mean": 0.0011, "season_amp": 0.16}, "crow": {"c_row": 12.0}, "vexpq": {"vexp_q": 0.9},
                "fc_roll": {"fc_mode": "roll"}, "fc_da": {"fc_mode": "dayahead", "roll_min_hist": 1}, "fc_perfect": {"fc_mode": "perfect"}}
    for name, over in variants.items():
        cfg = dict(base, **over); i2 = sim.planner_inputs("ppa", cfg)
        for pol, par in (POLICIES[5], POLICIES[4], POLICIES[3]):
            res[f"variant|{name}|{pol}"] = run_one(pol, par, "ppa", 4, cfg, i2)
    cfg = dict(base, carry=True, wrap_horizon=True); i3 = sim.planner_inputs("merchant", cfg); st = None
    for k, off in enumerate((0, 10000, 20000)):
        r = sim.simulate("proposed", POLICIES[5][1], "merchant", 5 + off, cfg=cfg, clim=i3[0], vexp=i3[1], pbar=i3[2], init=st)
        st = r["state"]; res[f"carry|{k}"] = dict(net=r["net"], state={a: np.asarray(b) for a, b in st.items()})
    r = sim.simulate("proposed", POLICIES[5][1], "merchant", 6, cfg=dict(base, mission_log=True, diag=True, log_decisions=True, fc_mode="roll", roll_min_hist=1), clim=inp[0], vexp=inp[1], pbar=inp[2], record=True)
    res["logs"] = dict(missions=digest_text(r["missions"]), est=r["est_log"], sr=r["sr_log"], trace=r["trace"], decisions=digest_text(r["decisions"]), diag=digest_text(r["diag"]))
    with Pool(4) as pool:
        rn = api.runner(pool, [1000, 1001], list(range(4)), TINY_GRID)
        best = rn.tune_params("merchant", cfg_over=SMALL, policies=list(TINY_GRID))
        res["tune_evaluate"] = dict(best=best, ev=rn.evaluate_summary("merchant", best, cfg_over=SMALL, policies=list(TINY_GRID)))
    return res


def _fold(pool, mk, c, fold, extra=None):
    return chrono_study.run_fold(api.runner(pool, [1000, 1001], [0, 1, 2], TINY_GRID), mk, c, fold, extra=extra)


def chrono():
    """Chronological replay: the R1 fold on interval values, and the older hourly replay on real_market."""
    res = {}
    with Pool(4) as pool:
        for mk, c, f in (("SA1_aligned", "merchant", "Y2"), ("ES_raw", "ppa", "Y3")):
            res[f"{mk}|{c}|{f}"] = _fold(pool, mk, c, f)
    for c in ("merchant", "ppa"):
        otr = {"real_market": "QLD1_aligned", "real_years": (0, 2), "vexp_q": 0.99}; ote = {"real_market": "QLD1_aligned", "real_years": (1,), "vexp_q": 0.99}
        icfg = dict(sim.CONFIG, **otr); cfg = dict(sim.CONFIG, **ote); inp = sim.planner_inputs(c, icfg)
        res[f"hourly|{c}|inputs"] = inp
        for pol, par in POLICIES[1:6]:
            res[f"hourly|{c}|{pol}"] = run_one(pol, par, c, 0, cfg, inp)
    z = dict(real_value="SA1_raw", real_years=(1,), fc_mode="roll", roll_min_hist=1)
    val, warm = sim.contract_value("merchant", 0, dict(sim.CONFIG, **z))
    hh = np.arange(24 * 40, 24 * 40 + 168)
    res["forecasts"] = {m: sim.fc_value(m, 40, hh, val, val, 1, warm) for m in ("clim", "roll", "dayahead", "perfect")}
    res["forecast_nowarm"] = {m: forecasting.value_forecast(m, 40, hh, val, val, min_hist=1) for m in ("clim", "roll", "dayahead", "perfect")}
    return res


def matched():
    """Matched sites: site years on the price clock, per-fold climatology and two replay folds."""
    res = {}
    for mk in mr.MARKETS:
        cfg = dict(sim.CONFIG, **mr.site_over(mk, 2025), real_value=mk)
        res[f"site|{mk}"] = {k: v for k, v in sim.site_year(2024, cfg).items()}
        res[f"clim|{mk}"] = sim.climatology_pdc(cfg)
    res["fold_test_year"] = [mr.fold_test_year(f) for f in mr.FOLD_NAMES]
    with Pool(4) as pool:
        for mk, c, f in (("SA1_raw", "merchant", "Y2"), ("ES_raw", "ppa", "Y3"), ("QLD1_raw", "ppa", "Y2")):
            res[f"{mk}|{c}|{f}"] = _fold(pool, mk, c, f, extra=mr.site_over(mk, mr.fold_test_year(f), 0.0030))
    return res


def robot():
    """Robot sweep: the sweep cell at each kind of setting, mission packing and schedule checks."""
    res = {}
    settings = {"default": {}, "night240": {"night_min": 240.0}, "service40": {"service_min": 40.0}, "speed0.25": {"speed_mps": 0.25}, "battery6": {"battery_rows": 6}, "avail0.8": {"availability": 0.8}}
    with Pool(4) as pool:
        rn = api.runner(pool, [1000, 1001], [0, 1, 2], TINY_GRID)
        for setting, over in settings.items():
            res[setting] = rs.cell(rn, setting, over, "merchant", ["fixed", "threshold", "econ", "ft", "proposed"])
            res[f"rows_per_night|{setting}"] = rs.rows_per_night(over)
    cfg = dict(sim.CONFIG, battery_rows=3)
    res["pack"] = sim.pack(list(range(39, -1, -3)), cfg)
    res["mission_time"] = sim.mission_time([3, 9, 20], cfg)
    res["violations"] = checks.schedule_violations([(61, [1, 3]), (61, [2]), (10, [39, 39])], cfg)
    return res


def row_tables_in(seed, contract, cfg, world):
    return exact.row_tables(seed, contract, cfg, world=world)


def exact_benchmark():
    """Exact benchmark: row tables, full MILP, both receding-horizon optimisers, and the belief world."""
    res = {}
    for contract in ("fixed", "merchant"):
        cfg = dict(sim.CONFIG, n_rows=4, night_min=100.0, d0=120, d1=144, c_row=4.0)
        c, v, p = sim.planner_inputs(contract, cfg)
        Rev = exact.row_tables(0, contract, cfg); Rb = exact.row_tables(0, contract, cfg, belief=(c, v))
        r, sched = exact.solve(Rev, cfg, 120)
        res[f"{contract}|tables"] = [Rev, Rb]
        res[f"{contract}|solve"] = dict(status=int(r.status), sched=sched, value=exact.schedule_value(Rev, sched, cfg), none=exact.schedule_value(Rev, [], cfg), viol=checks.schedule_violations(sched, cfg))
        res[f"{contract}|inc"] = exact.expected_increment(cfg)
        a = sim.simulate("mpc", {"fn": exact.make_mpc(7)}, contract, 1, cfg=cfg, clim=c, vexp=v, pbar=p)
        lg = []
        b = sim.simulate("mpc", {"fn": optimisation.make_mpc(horizon=7, tail=3, log=lg, time_limit=60.0, gap=1e-4, oracle_expo=True)}, contract, 1, cfg=cfg, clim=c, vexp=v, pbar=p)
        res[f"{contract}|mpc"] = dict(a=[a["net"], a["sched"]], b=[b["net"], b["sched"]], status=[x["status"] for x in lg])
        w = belief_world(c, v)
        Rw = row_tables_in(0, contract, cfg, w)
        r2, s2 = exact.solve(Rw, cfg, 120)
        res[f"{contract}|belief"] = dict(tables=Rw, sched=s2, value=exact.schedule_value(Rw, s2, cfg), run=sim.simulate("threshold", {"theta": 0.03}, contract, 0, info="perfect", cfg=cfg, clim=c, vexp=v, pbar=p, world=w)["net"])
    return res


CASES = dict(generated=generated, chrono=chrono, matched=matched, robot=robot, exact=exact_benchmark)
NEEDS_DATA = ("chrono", "matched")
