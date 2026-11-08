"""One simulated year: information update, tonight's decision, production and revenue, soiling and rain."""
from __future__ import annotations
from typing import Any
import numpy as np
from pvclean.config import CONFIG
from pvclean.forecasts import forecast_record
from pvclean.markets import contract_value
from pvclean.contracts import get_contract
from pvclean.policies import State, make_policy
from .accounting import Ledger
from .plant import delivered, export_limit, row_ac
from .robot import blackout_mask, mission_record, robot_up
from .soiling import rain_recovery
from .world import DEFAULT_WORLD, World

STATE_KEYS = ("sr", "est", "k_hat", "last_meas", "site_since", "tau", "A")


def simulate(policy: str, params: dict[str, Any], contract: str, seed: int, info: str = "site", sigma: float = 0.01, cfg: dict[str, Any] = CONFIG,
             hetero: float = 1.0, clim: np.ndarray | None = None, vexp: np.ndarray | None = None, pbar: float | None = None, record: bool = False,
             init: dict[str, Any] | None = None, world: World = DEFAULT_WORLD) -> dict[str, Any]:
    """Runs one year of `policy` under `contract` and returns its annual outcomes.

    info: 'site' (fixed reference station), 'mobile' (row inspection every patrol_every days, noise sigma), 'perfect' (true row state, an upper reference only).
    clim: planner production forecast (8760,); vexp: planner expected value per hour (8760,); pbar: constant price of the econ baseline.
    init: out['state'] of a previous year run with cfg carry=True: continuous operation, no clean reset.
    world: the functions that define what is true (see pvclean.core.world).
    cfg options: station_bias (relative bias of the station's site increment), wrap_horizon (horizons run past day 364 into the next year's climatology), battery_rows
    (rows per mission), availability (probability the robot can work on a night), mission_log (adds out['missions'], out['est_log'], out['sr_log']), diag (adds out['diag'];
    no effect on decisions), log_decisions (adds out['decisions'])."""
    n = cfg["n_rows"]
    pol = make_policy(policy, params)
    w = world.weather(seed, cfg)
    pdc, rain = w["pdc"], w["rain"]
    val, warm = contract_value(contract, seed, cfg, world.hourly_value)
    capped = get_contract(contract).capped
    inc, row_noise = world.dust(seed, cfg)
    expo = world.exposure(cfg, hetero=hetero)
    fc = world.rain_forecast(rain, seed, cfg)
    black = blackout_mask(cfg)
    up = robot_up(seed, cfg)
    rng = np.random.default_rng(seed + cfg["seed_offset_info"])
    sr_clean = 1.0 - cfg["clean_residual"]

    s = State(); s.seed = seed
    s.cfg, s.n, s.black, s.fc, s.clim, s.vexp, s.pbar, s.val, s.warm, s.pdc = cfg, n, black, fc, clim, vexp, pbar, val, warm, pdc
    s.capped, s.lim, s.sr_clean, s.H, s.wrap = capped, export_limit(cfg), sr_clean, cfg["horizon_days"] * 24, bool(cfg.get("wrap_horizon"))
    s.expo, s.inc, s.rain, s.row_noise = expo, inc, rain, row_noise
    sr = np.full(n, sr_clean)          # true state
    s.est = np.full(n, sr_clean)       # planner estimate
    k_hat = np.ones(n)                 # planner's exposure estimate (mobile information learns it)
    last_meas = np.full(n, sr_clean); site_since = np.zeros(n)
    s.tau = np.zeros(n)
    s.A = np.zeros(n)
    s.last_clean = np.full(n, -10_000 if "d0" not in cfg else cfg["d0"])
    if init is not None:
        sr, s.est, k_hat, last_meas, site_since, s.tau, s.A = (np.array(init[k], float) for k in STATE_KEYS)
        s.last_clean = np.array(init["last_clean"], float) - 365
    sched: list[tuple[int, list[int]]] = []
    dlog: list[dict[str, Any]] = []
    led = Ledger()
    bias = 1.0 + cfg.get("station_bias", 0.0)
    trace: list[np.ndarray] = []
    diag: list[dict[str, Any]] | None = [] if cfg.get("diag") else None
    mlog = cfg.get("mission_log")
    missions: list[dict[str, Any]] = []; est_log: list[np.ndarray] = []; sr_log: list[np.ndarray] = []

    for d in range(cfg.get("d0", 0), cfg.get("d1", 365)):
        hs = slice(d * 24, d * 24 + 24)
        s.d = d
        s.dg = {} if diag is not None else None

        # information update (start of night d-1 -> d)
        if info == "perfect":
            s.est = sr.copy()
        elif info == "mobile" and d % cfg["patrol_every"] == 0 and pol.inspects:
            meas = np.clip(sr + rng.normal(0, sigma, n), *cfg["mobile_measure_clip"])
            dl = last_meas - meas       # learn row exposure from the loss since the previous measurement
            ok = site_since > cfg["mobile_min_site_loss"]
            k_obs = np.where(ok, np.clip(dl / np.maximum(site_since, cfg["mobile_ratio_floor"]), *cfg["mobile_k_clip"]), k_hat)
            k_hat = np.where(ok, cfg["mobile_k_keep"] * k_hat + cfg["mobile_k_new"] * k_obs, k_hat)
            s.est = meas.copy(); last_meas = meas.copy(); site_since[:] = 0
            led.inspection(n, cfg)

        # tonight's cleaning
        s.avail = ~black[d]
        if mlog:
            est_log.append(s.est.copy()); sr_log.append(sr.copy())
        dec = pol.decide(s)
        rows = list(dec.rows) if up[d] else []
        if cfg.get("log_decisions"):
            dlog.append(dict(day=d, rows=list(map(int, rows)), **forecast_record(cfg.get("fc_mode", "clim"), d, s.H)))

        if rows:
            led.mission(len(rows), cfg)
            sched.append((d, list(map(int, rows))))
            if mlog:
                wanted = np.zeros(n, bool) if dec.wanted is None else dec.wanted
                missions.append(mission_record(d, rows, np.where(wanted & ~s.avail)[0], dec.reason, cfg))
            r = np.array(rows)
            sr[r] = sr_clean; s.est[r] = sr_clean; last_meas[r] = sr_clean
            s.tau[r] = 0; s.A[r] = 0; s.last_clean[r] = d; site_since[r] = 0

        # day d production and revenue
        ac = row_ac(pdc[hs], sr, cfg)
        dl = delivered(ac, cfg, capped)
        led.revenue += float((dl * val[hs]).sum()); led.energy += float(dl.sum())
        if diag is not None:
            diag.append(dict(day=d, rows=list(map(int, rows)), avail=s.avail.copy(), rain=float(rain[d]), v_day=float(val[hs].mean()),
                             net_day=float((dl * val[hs]).sum()) - (cfg["c_mission"] + cfg["c_row"] * len(rows) if rows else 0.0), **s.dg))
        pol.book(s, hs)
        s.tau += 1

        # end of day: soiling and rain
        dloss = inc[d] * expo * row_noise[d]
        sr = np.maximum(cfg["sr_floor"], sr - dloss)
        if info == "site":
            s.est = np.maximum(cfg["sr_floor"], s.est - inc[d] * bias)   # the station sees the site increment
        elif info == "mobile":
            s.est = np.maximum(cfg["sr_floor"], s.est - inc[d] * k_hat)
            site_since += inc[d]
        rec = rain_recovery(rain[d], cfg)
        if rec > 0:
            sr = sr + rec * (sr_clean - sr)
            s.est = s.est + rec * (sr_clean - s.est)
            if rec >= cfg["rain_reset_recov"]:
                s.tau[:] = 0; s.A[:] = 0
        if record:
            trace.append(sr.copy())

    out = led.summary()
    out["sched"] = sched
    if cfg.get("log_decisions"):
        out["decisions"] = dlog
    out["net"] = led.net
    if diag is not None:
        out["diag"] = diag
    if mlog:
        out.update(missions=missions, est_log=np.array(est_log), sr_log=np.array(sr_log))
    if cfg.get("carry"):
        out["state"] = dict(zip(STATE_KEYS, (sr, s.est, k_hat, last_meas, site_since, s.tau, s.A)), last_clean=s.last_clean)
    if record:
        out["trace"] = np.array(trace)
    return out
