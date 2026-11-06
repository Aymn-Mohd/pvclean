"""Row revenue tables of the exact benchmark. A row's output depends only on its last reset day, so a row's schedule is a path through reset days."""
from __future__ import annotations
from typing import Any, Iterable, Sequence
import numpy as np
from pvclean.core.plant import row_ac
from pvclean.core.soiling import rain_recovery
from pvclean.core.world import DEFAULT_WORLD, World
from pvclean.markets import spot_prices


def row_tables(seed: int, contract: str, cfg: dict[str, Any], belief: tuple[np.ndarray, np.ndarray] | None = None, world: World = DEFAULT_WORLD) -> np.ndarray:
    """Rev[i][c][d]: revenue of row i on day d if its last reset was on day c (c = d0 is the free start).
    belief = (clim, vexp) gives the information-matched model: what the station-information planner knows, with the site increment and rain as observed and equal row exposure."""
    n, d0, d1 = cfg["n_rows"], cfg["d0"], cfg["d1"]
    w = world.weather(seed, cfg); pdc, rain = w["pdc"], w["rain"]
    val = world.hourly_value(contract, spot_prices(seed, cfg), cfg)
    inc, rn = world.dust(seed, cfg); expo = world.exposure(cfg)
    if belief is not None:
        clim, vexp = belief
        pdc, val = clim, vexp
        expo = np.ones(n); rn = np.ones_like(rn)
    sc = 1.0 - cfg["clean_residual"]
    D = d1 - d0
    Rev = np.zeros((n, D, D))
    for c in range(d0, d1):
        sr = np.full(n, sc)
        for d in range(c, d1):
            hs = slice(d * 24, d * 24 + 24)
            ac = row_ac(pdc[hs], sr, cfg)
            Rev[:, c - d0, d - d0] = (ac * val[hs][None, :]).sum(1)
            sr = np.maximum(cfg["sr_floor"], sr - inc[d] * expo * rn[d])
            rec = rain_recovery(rain[d], cfg)
            if rec > 0:
                sr = sr + rec * (sc - sr)
    return Rev


def schedule_value(Rev: np.ndarray, sched: Iterable[tuple[int, Sequence[int]]], cfg: dict[str, Any]) -> float:
    """Revenue minus cleaning and mission cost of a schedule."""
    n, d0, d1 = cfg["n_rows"], cfg["d0"], cfg["d1"]
    last = np.full(n, d0); tot = 0.0; cost = 0.0
    byday = {d: rows for d, rows in sched}
    for d in range(d0, d1):
        if d in byday and byday[d]:
            for r in byday[d]:
                last[r] = d
            cost += cfg["c_mission"] + cfg["c_row"] * len(byday[d])
        for i in range(n):
            tot += Rev[i, last[i] - d0, d - d0]
    return tot - cost
