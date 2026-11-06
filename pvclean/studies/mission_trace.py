"""Phase R2 step 4: one-year mission trace for the figure (EXTENSION / DESCRIPTIVE). Merchant contract, default robot, tuned parameters from
results/results_robot.json.

Seed: test seeds sorted by planner net value; with 50 seeds the median falls between two, so the lower middle one (rank 25 of 50) is used.
Representative night: among missions of at least 4 rows on nights with closed rows, the one whose size is closest to the median mission
size (earliest on ties); if there is none, the same rule over all missions of at least 4 rows. Week: the night and three nights either side,
shifted to stay inside the year.
Export: rows are numbered 1-40 (sim index + 1). The soiling ratio of a night is the value when that night's decision is taken. Times are
minutes from the opening of the night window. sim.mission_time charges (index + 1) pitches from the dock, so the dock sits one pitch (10 m)
before row 1. Writes results/trace_merchant_default.json."""
from __future__ import annotations
from typing import Any
from pvclean import model
import numpy as np
from .study import Study



def one_based(m: Any) -> Any:
    """A mission with rows numbered from 1."""
    m = dict(m, rows=[r + 1 for r in m["rows"]], skipped_closed=[r + 1 for r in m["skipped_closed"]],
             stops=[dict(s, row=s["row"] + 1) for s in m["stops"]])
    return m


def pick_night(missions: Any, black: Any) -> Any:
    """The representative night of the figure."""
    big = [m for m in missions if len(m["rows"]) >= 4]
    closed = [m for m in big if black[m["day"]].any()]
    pool = closed or big
    med = float(np.median([len(m["rows"]) for m in missions]))
    return min(pool, key=lambda m: (abs(len(m["rows"]) - med), m["day"])), bool(closed), med


def run(S: Study) -> dict:
    """The one-year trace of the median seed (trace_merchant_default.json)."""
    D = S.stored("results_robot.json")["default|merchant"]; test = S.protocol.test
    net = np.array(D["test"]["proposed"]["net"])
    seed = test[int(np.argsort(net, kind="stable")[len(net) // 2 - 1])]
    par = D["tuned"]["proposed"]["params"]
    cfg = dict(model.CONFIG, mission_log=True)
    clim, vexp, pbar = model.planner_inputs("merchant", dict(model.CONFIG))
    r = model.simulate("proposed", par, "merchant", seed, cfg=cfg, clim=clim, vexp=vexp, pbar=pbar)
    assert r["net"] == net[test.index(seed)], "trace does not reproduce the sweep"
    black = model.blackout_mask(cfg)
    night, used_closed, med = pick_night(r["missions"], black)
    d = night["day"]; d0 = min(max(d - 3, 0), 358)
    by_day = {m["day"]: m for m in r["missions"]}
    week = []
    for x in range(d0, d0 + 7):
        m = by_day.get(x)
        week.append(dict(day=x, date=str(np.datetime64(f"{cfg['year']}-01-01") + np.timedelta64(x, "D")), mission=one_based(m) if m else None,
                         closed_rows=[int(i) + 1 for i in np.where(black[x])[0]],
                         est_soiling_ratio=[float(v) for v in r["est_log"][x]], true_soiling_ratio=[float(v) for v in r["sr_log"][x]]))
    ms = r["missions"]
    out = dict(label="EXTENSION / DESCRIPTIVE", contract="merchant", robot_setting="default", seed=int(seed), planner_params=par,
               planner_net=float(r["net"]), median_rule="lower middle of 50 test seeds by planner net value",
               median_net_all_seeds=float(np.median(net)),
               night_rule="mission of >= 4 rows on a night with closed rows, size closest to the median mission size (earliest on ties)",
               night_rule_closed_used=used_closed, median_mission_rows=med,
               plant=dict(n_rows=cfg["n_rows"], row_pitch_m=cfg["row_pitch_m"], dock="beside row 1, one pitch before it", dock_position_m=0.0,
                          row_position_m=[cfg["row_pitch_m"] * (i + 1) for i in range(cfg["n_rows"])], row_numbering="1-40 = sim index + 1"),
               robot=dict(night_min=cfg["night_min"], service_min=cfg["service_min"], speed_mps=cfg["speed_mps"]),
               night=dict(day=d, date=night["date"], closed_rows=[int(i) + 1 for i in np.where(black[d])[0]],
                          est_soiling_ratio=[float(v) for v in r["est_log"][d]], **{k: v for k, v in one_based(night).items() if k not in ("day", "date")}),
               week=week, missions=[one_based(m) for m in ms],
               stats=dict(missions=len(ms), rows_cleaned=int(r["n_clean"]), mean_rows_per_mission=float(np.mean([len(m["rows"]) for m in ms])),
                          mean_night_use=float(np.mean([m["end_min"] / cfg["night_min"] for m in ms])), share_nights_worked=len(ms) / 365.0,
                          reasons={k: sum(m["reason"] == k for m in ms) for k in sorted({m["reason"] for m in ms})},
                          missions_on_closed_nights=sum(bool(black[m["day"]].any()) for m in ms),
                          rows_skipped_closed=sum(len(m["skipped_closed"]) for m in ms)))
    return out
