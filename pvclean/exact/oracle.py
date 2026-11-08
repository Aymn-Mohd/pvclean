"""Perfect-foresight schedule of a full plant-year: known weather, dust, row noise, prices and rain, with the same robot, night budget, access windows and costs as the simulator.
The subset MILP of milp.py cannot reach 40 rows and 365 nights: one night has about 1e10 feasible row sets. Here a row's value is a path through its reset nights, as in milp.py, and rows couple
only through the mission cost and the night budget. best_schedule() searches over the set of mission nights, with exact per-row dynamic programmes inside, and always returns a feasible schedule.
upper_bound() is a Lagrangian bound. The true optimum lies between the two. solve_oracle() runs both."""
from __future__ import annotations
from typing import Any
import numpy as np
from pvclean.core.robot import blackout_mask, mission_time
from pvclean.core.soiling import rain_recovery
from pvclean.core.world import DEFAULT_WORLD, World
from pvclean.markets import contract_value


def window(cfg: dict[str, Any]) -> tuple[int, int]:
    """First day and number of days."""
    d0 = cfg.get("d0", 0)
    return d0, cfg.get("d1", 365) - d0


def sr_tables(seed: int, cfg: dict[str, Any], world: World = DEFAULT_WORLD) -> np.ndarray:
    """SR[k, i, c]: soiling ratio of row i on window day k if its last reset was window night c <= k (c = 0 is the clean start). The update order is the simulator's."""
    n = cfg["n_rows"]; d0, D = window(cfg)
    rain = world.weather(seed, cfg)["rain"]
    inc, rn = world.dust(seed, cfg); expo = world.exposure(cfg)
    sc = 1.0 - cfg["clean_residual"]
    SR = np.zeros((D, n, D)); cur = np.full((n, D), sc)
    for k in range(D):
        d = d0 + k; a = cur[:, :k + 1]
        SR[k, :, :k + 1] = a
        a = np.maximum(cfg["sr_floor"], a - (inc[d] * expo * rn[d])[:, None])
        rec = rain_recovery(rain[d], cfg)
        if rec > 0:
            a = a + rec * (sc - a)
        cur[:, :k + 1] = a
    return SR


def path_values(seed: int, contract: str, cfg: dict[str, Any], SR: np.ndarray | None = None, world: World = DEFAULT_WORLD) -> np.ndarray:
    """G[i, c, e]: revenue of row i over window days c .. e-1 with last reset c."""
    n = cfg["n_rows"]; d0, D = window(cfg)
    if SR is None:
        SR = sr_tables(seed, cfg, world)
    pdc = world.weather(seed, cfg)["pdc"]; val = contract_value(contract, seed, cfg, world.hourly_value)[0]
    cap = cfg["row_kwp"] / cfg["dc_ac"]; kwp = cfg["row_kwp"]
    G = np.zeros((n, D, D + 1))
    for k in range(D):
        d = d0 + k; p = pdc[d * 24:d * 24 + 24]; v = val[d * 24:d * 24 + 24]
        r = np.zeros((n, k + 1))
        for h in np.flatnonzero((p > 0) & (v != 0)):
            r += np.minimum(cap, kwp * p[h] * SR[k, :, :k + 1] * cfg["inv_eff"]) * v[h]
        G[:, :k + 1, k + 1] = G[:, :k + 1, k] + r
    return G


def row_dp(G: np.ndarray, cost: np.ndarray, nights: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Best path of every row over reset nights `nights` (ascending, without 0). cost[i, t]: price of resetting row i on night t, np.inf if it cannot. Returns (values, next-node table, nodes)."""
    n, D = G.shape[0], G.shape[1]
    nodes = np.r_[0, nights].astype(int); m = len(nodes)
    sub = G[:, nodes[:, None], nodes[None, :]]            # (n, m, m): revenue from node a to node b
    end = G[:, nodes, D]
    cn = cost[:, nodes]
    W = np.zeros((n, m)); nxt = np.full((n, m), -1); ar = np.arange(n)
    for a in range(m - 1, -1, -1):
        best = end[:, a]
        if a < m - 1:
            cand = sub[:, a, a + 1:] - cn[:, a + 1:] + W[:, a + 1:]
            j = cand.argmax(1); v = cand[ar, j]; take = v > best
            nxt[:, a] = np.where(take, a + 1 + j, -1); best = np.where(take, v, best)
        W[:, a] = best
    return W[:, 0], nxt, nodes


def paths_of(nxt: np.ndarray, nodes: np.ndarray) -> list[list[int]]:
    """Reset nights of each row."""
    out = []
    for i in range(nxt.shape[0]):
        a = 0; p = []
        while nxt[i, a] >= 0:
            a = int(nxt[i, a]); p.append(int(nodes[a]))
        out.append(p)
    return out


def evaluate(G: np.ndarray, base: np.ndarray, nights: np.ndarray, cfg: dict[str, Any]) -> tuple[float, dict[int, list[int]]]:
    """Value of a set of mission nights with the night budget enforced: on an over-full night the rows that lose least drop out, and the rows are solved again. Empty nights are not charged."""
    cost = base; c_m = cfg["c_mission"]
    while True:
        vals, nxt, nodes = row_dp(G, cost, nights)
        by: dict[int, list[int]] = {}
        for i, p in enumerate(paths_of(nxt, nodes)):
            for t in p:
                by.setdefault(t, []).append(i)
        over = [t for t, r in by.items() if mission_time(sorted(r), cfg) > cfg["night_min"]]
        if not over:
            return float(vals.sum()) - c_m * len(by), by
        cost = cost.copy()
        for t in over:
            c2 = cost.copy(); c2[:, t] = np.inf
            loss = vals - row_dp(G, c2, nights)[0]
            rows = sorted(by[t], key=lambda i: loss[i])
            keep = list(by[t])
            for i in rows:
                if mission_time(sorted(keep), cfg) <= cfg["night_min"]:
                    break
                keep.remove(i); cost[i, t] = np.inf


def base_cost(cfg: dict[str, Any]) -> np.ndarray:
    """Row price per window night, with closed rows at infinity."""
    n = cfg["n_rows"]; d0, D = window(cfg)
    c = np.full((n, D), float(cfg["c_row"]))
    c[blackout_mask(cfg)[d0:d0 + D].T] = np.inf
    return c


def local_search(G: np.ndarray, cfg: dict[str, Any], start: list[int], passes: int = 8) -> tuple[float, dict[int, list[int]]]:
    """Add, drop and shift mission nights until no move helps. Every state is a feasible schedule."""
    D = window(cfg)[1]; base = base_cost(cfg)
    M = sorted(set(start)); val, by = evaluate(G, base, np.array(M, int), cfg); M = sorted(by)
    for _ in range(passes):
        changed = False
        for t in range(1, D):
            if t not in M:
                v, b = evaluate(G, base, np.array(sorted(M + [t]), int), cfg)
                if v > val + 1e-9:
                    val, by, changed = v, b, True; M = sorted(b)
        for t in list(M):
            for alt in (None, -1, 1, -2, 2, -3, 3, -5, 5, -8, 8):
                if t not in M:
                    break
                rest = [x for x in M if x != t]
                if alt is not None:
                    s = t + alt
                    if s < 1 or s >= D or s in M:
                        continue
                    rest = sorted(rest + [s])
                v, b = evaluate(G, base, np.array(rest, int), cfg)
                if v > val + 1e-9:
                    val, by, changed = v, b, True; M = sorted(b)
                    break
        if not changed:
            break
    return val, by


def cap_rows(cfg: dict[str, Any]) -> int:
    """The most rows any one night can hold: the nearest rows fit best, so this relaxes the night budget validly."""
    k = 0
    while k < cfg["n_rows"] and mission_time(list(range(k + 1)), cfg) <= cfg["night_min"]:
        k += 1
    return k


def upper_bound(G: np.ndarray, cfg: dict[str, Any], incumbent: float, iters: int = 400) -> tuple[float, np.ndarray]:
    """Lagrangian bound. The link x[i,t] <= y[t] has multiplier lam[i,t] and the row limit sum_i x[i,t] <= K y[t] has mu[t]: rows pay for nights and nights collect the payments. Any non-negative
    multipliers give a valid bound, so the best one seen is returned, with the mean number of rows each night drew over the last iterations."""
    d0, D = window(cfg); n = cfg["n_rows"]; K = cap_rows(cfg); cm = cfg["c_mission"]
    closed = blackout_mask(cfg)[d0:d0 + D].T; nights = np.arange(1, D)
    lam = np.full((n, D), cm / n); mu = np.zeros(D); best = np.inf; scale = 1.0; since = 0; use = np.zeros(D); seen = 0
    for it in range(iters):
        cost = np.where(closed, np.inf, cfg["c_row"] + lam + mu[None, :])
        vals, nxt, nodes = row_dp(G, cost, nights)
        x = np.zeros((n, D))
        for i, p in enumerate(paths_of(nxt, nodes)):
            x[i, p] = 1
        gain = np.where(closed, 0.0, lam).sum(0) + K * mu - cm; gain[0] = 0
        y = (gain > 0).astype(float)
        L = float(vals.sum()) + float(np.maximum(gain, 0).sum())
        if L < best - 1e-9:
            best = L; since = 0
        else:
            since += 1
            if since >= 8:
                scale *= 0.7; since = 0
        if it >= iters // 2:
            use += x.sum(0); seen += 1
        g1 = y[None, :] - x; g1[closed] = 0; g1[:, 0] = 0
        g2 = K * y - x.sum(0); g2[0] = 0
        nrm = float((g1 ** 2).sum() + (g2 ** 2).sum())
        if nrm == 0:
            break
        step = scale * max(L - incumbent, 1e-3) / nrm
        lam = np.maximum(0, lam - step * g1); mu = np.maximum(0, mu - step * g2)
    return best, use / max(seen, 1)


def solve_oracle(G: np.ndarray, cfg: dict[str, Any], starts: list[list[int]] | None = None, iters: int = 400) -> dict[str, Any]:
    """Best feasible schedule and an upper bound, as revenue minus costs. `starts`: mission nights of known feasible schedules, tried as extra starting points."""
    D = window(cfg)[1]; base = base_cost(cfg)
    v0 = evaluate(G, base, np.arange(7, D, 7), cfg)[0] if D > 7 else float(G[:, 0, D].sum())
    ub, use = upper_bound(G, cfg, v0, iters)
    cands = [[int(t) for t in np.flatnonzero(use >= q)] for q in (0.5, 1.0, 2.0, 4.0)] + (starts or [])
    scored = sorted(((evaluate(G, base, np.array(sorted(set(c)), int), cfg)[0], k) for k, c in enumerate(cands)), reverse=True)
    val = -np.inf; by: dict[int, list[int]] = {}
    # The two best built candidates, and every given start: a start can rank below them before the search and above them after it.
    for k in sorted({k for _, k in scored[:2]} | set(range(len(cands) - len(starts or []), len(cands)))):
        v, b = local_search(G, cfg, cands[k])
        if v > val:
            val, by = v, b
    ub2 = upper_bound(G, cfg, val, iters)[0]
    return dict(value=val, upper=min(ub, ub2), sched=[(int(t), sorted(int(i) for i in by[t])) for t in sorted(by)])
