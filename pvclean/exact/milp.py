"""Exact clairvoyant optimum on small instances: known weather, dust, rain and prices. Missions couple rows through the time budget, mission cost and access windows.
Solved with HiGHS through scipy.optimize.milp."""
from __future__ import annotations
import itertools
from typing import Any
import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import lil_matrix
from pvclean.core.robot import blackout_mask, mission_time


def feasible_subsets(cfg: dict[str, Any]) -> list[tuple[int, ...]]:
    """Every row set that one mission can clean within the night budget."""
    n = cfg["n_rows"]
    return [S for k in range(1, n + 1) for S in itertools.combinations(range(n), k) if mission_time(list(S), cfg) <= cfg["night_min"]]


def solve(Rev: np.ndarray, cfg: dict[str, Any], time_limit: float = 120) -> tuple[Any, list[tuple[int, list[int]]]]:
    """The optimal schedule for a revenue table. Returns (solver result, schedule). The row cost is charged through the mission variables."""
    n, d0, d1 = cfg["n_rows"], cfg["d0"], cfg["d1"]
    D = d1 - d0
    black = blackout_mask(cfg)
    subsets = feasible_subsets(cfg)
    # variable layout: z[i,c,c'] for c<c' in 0..D (c'=D is the end), then y[S,t] for t in 1..D-1
    idx: dict[tuple, int] = {}; obj: list[float] = []

    def add(key: tuple, cost: float) -> None:
        idx[key] = len(obj); obj.append(cost)
    for i in range(n):
        for c in range(D):
            for c2 in range(c + 1, D + 1):
                add(("z", i, c, c2), -Rev[i, c, c:c2].sum() + 0.0)
    for t in range(1, D):
        for S in subsets:
            add(("y", S, t), cfg["c_mission"] + cfg["c_row"] * len(S))
    N = len(obj)
    lo: list[int] = []; hi: list[int] = []
    A = lil_matrix((n * (D + 1) + (D - 1) * (n + 1), N)); r = 0
    for i in range(n):
        # flow: start node 0 sends 1; node c in 1..D-1 in = out; end node receives 1
        for c2 in range(1, D + 1):
            A[r, idx[("z", i, 0, c2)]] += 1
        lo.append(1); hi.append(1); r += 1
        for c in range(1, D):
            for c0 in range(c):
                A[r, idx[("z", i, c0, c)]] += 1
            for c2 in range(c + 1, D + 1):
                A[r, idx[("z", i, c, c2)]] -= 1
            lo.append(0); hi.append(0); r += 1
    for t in range(1, D):
        for i in range(n):          # x[i,t] = sum_{S in i} y[S,t]
            for c0 in range(t):
                A[r, idx[("z", i, c0, t)]] += 1
            for S in subsets:
                if i in S: A[r, idx[("y", S, t)]] -= 1
            lo.append(0); hi.append(0); r += 1
        for S in subsets:
            A[r, idx[("y", S, t)]] += 1
        lo.append(0); hi.append(1); r += 1
    A = A[:r].tocsr()
    ub = np.ones(N)
    for t in range(1, D):           # access windows: closed rows cannot be cleaned
        for S in subsets:
            if any(black[d0 + t, i] for i in S):
                ub[idx[("y", S, t)]] = 0
    res = milp(c=np.array(obj), constraints=LinearConstraint(A, lo, hi), integrality=np.ones(N),
               bounds=Bounds(np.zeros(N), ub), options=dict(time_limit=time_limit, disp=False, mip_rel_gap=1e-4))
    sched: list[tuple[int, list[int]]] = []
    if res.x is not None:
        for t in range(1, D):
            rows: list[int] = []
            for S in subsets:
                if res.x[idx[("y", S, t)]] > 0.5:
                    rows = list(S)
            if rows: sched.append((d0 + t, rows))
    return res, sched
