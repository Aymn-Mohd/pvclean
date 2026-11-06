"""Robot missions and access windows: mission time, packing, closed rows, availability, the mission log and schedule checks."""
from __future__ import annotations
from typing import Any, Iterable, Sequence
import numpy as np
import pandas as pd


def mission_time(rows: Sequence[int], cfg: dict[str, Any]) -> float:
    """Minutes for one mission: travel to the farthest row and back, plus service."""
    if len(rows) == 0:
        return 0.0
    far = max(rows) + 1
    travel = 2 * cfg["row_pitch_m"] * far / cfg["speed_mps"] / 60.0
    return travel + cfg["service_min"] * len(rows)


def pack(order: Iterable[int], cfg: dict[str, Any]) -> list[int]:
    """Greedy feasible set in priority order under the night time budget and cfg battery_rows (rows per mission, None = unlimited)."""
    cap = cfg.get("battery_rows")
    chosen: list[int] = []
    for r in order:
        if cap is not None and len(chosen) >= cap:
            break
        if mission_time(chosen + [r], cfg) <= cfg["night_min"]:
            chosen.append(r)
    return chosen


def blackout_mask(cfg: dict[str, Any]) -> np.ndarray:
    """(365, n_rows) mask of closed rows: crop work closes the odd rows in each window."""
    m = np.zeros((365, cfg["n_rows"]), bool)
    for s, L in cfg["blackouts"]:
        m[s:s + L, 1::2] = True
    return m


def robot_up(seed: int, cfg: dict[str, Any]) -> np.ndarray:
    """Nights the robot can work, from its own seeded stream: every availability level thresholds the same draws, so a lower level only adds down nights."""
    return np.random.default_rng(seed + cfg["seed_offset_robot"]).random(365) < cfg.get("availability", 1.0)


def mission_record(d: int, rows: Sequence[int], closed: Sequence[int], reason: str | None, cfg: dict[str, Any]) -> dict[str, Any]:
    """One mission of the cfg mission_log. The robot leaves the dock when the night window opens (start_min = 0, minutes from the opening: the simulator has no wall
    clock), cleans on one outbound sweep in ascending row order, the only order consistent with mission_time, and returns from the farthest row. Rows are 0-based as
    in out['sched']; day d is the night before production day d, and date is that production day."""
    leg = cfg["row_pitch_m"] / cfg["speed_mps"] / 60.0
    t = 0.0; pos = 0; stops = []
    for r in sorted(map(int, rows)):
        t += leg * (r + 1 - pos); pos = r + 1
        stops.append(dict(row=r, arrive_min=t, depart_min=t + cfg["service_min"]))
        t += cfg["service_min"]
    service = cfg["service_min"] * len(rows)
    return dict(day=d, date=str((pd.Timestamp(cfg["year"], 1, 1) + pd.Timedelta(days=d)).date()), rows=[s_["row"] for s_ in stops],
                stops=stops, start_min=0.0, end_min=mission_time(list(map(int, rows)), cfg), travel_min=2 * leg * pos,
                service_min=service, skipped_closed=list(map(int, closed)), reason=reason)


def schedule_violations(sched: Iterable[tuple[int, Sequence[int]]], cfg: dict[str, Any]) -> int:
    """Number of violated robot constraints in a list of (day, rows): night budget, battery limit, access windows, duplicates, range."""
    black = blackout_mask(cfg)
    n = cfg["n_rows"]; viol = 0; days = set()
    for d, rows in sched:
        if d in days: viol += 1
        days.add(d)
        if len(set(rows)) != len(rows) or any((r < 0 or r >= n) for r in rows): viol += 1
        if mission_time(list(rows), cfg) > cfg["night_min"] + 1e-9: viol += 1
        if cfg.get("battery_rows") is not None and len(rows) > cfg["battery_rows"]: viol += 1
        if any(black[d, r] for r in rows): viol += 1
        if d < cfg.get("d0", 0) or d >= cfg.get("d1", 365): viol += 1
    return viol
