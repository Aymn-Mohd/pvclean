"""Receding-horizon MILP with configurable information, horizon and terminal value. Each decision day solves a per-row path formulation with mission subsets.
A solution is only called optimal if status == 0 and the relative gap is below the requested tolerance."""
from __future__ import annotations
import time
from typing import Any, Callable
import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import lil_matrix
from pvclean.core.plant import row_ac
from pvclean.core.robot import blackout_mask
from pvclean.core.soiling import expected_increment
from pvclean.forecasts import value_forecast
from .milp import feasible_subsets


def make_mpc(horizon: int = 14, tail: int = 0, price_mode: str = "clim", min_hist: int = 7, time_limit: float = 20.0, gap: float = 1e-3, oracle_expo: bool = False,
             oracle_inc: bool = False, oracle_pdc: bool = False, log: list | None = None) -> Callable[..., list[int]]:
    """A decision function for the `mpc` policy. horizon = decision days; tail = further days valued with no further cleaning; price_mode = forecast; the oracle flags give the
    solver true row exposure, dust or production, and are used only in diagnostic arms. `log` receives the solver status, gap, objective, bound and runtime of each solve."""
    cache: dict[str, Any] = {}

    def decide(d, est, avail, cfg, clim, vexp, ctx):
        n, d1 = cfg["n_rows"], cfg.get("d1", 365)
        H = min(horizon, d1 - d)                 # decision nodes
        HH = min(H + tail, d1 - d) if tail else H  # valuation horizon (terminal tail, no further cleaning)
        black = blackout_mask(cfg)
        if "subs" not in cache:
            cache["inc"] = expected_increment(cfg)
            cache["subs"] = feasible_subsets(cfg)
        subs = cache["subs"]
        inc = ctx["inc"] if oracle_inc else cache["inc"]
        expo = ctx["expo"] if oracle_expo else np.ones(n)
        pdc = ctx["pdc"] if oracle_pdc else clim
        sc = 1.0 - cfg["clean_residual"]
        hh = np.arange(d * 24, (d + HH) * 24)
        vfc = value_forecast(price_mode, d, hh, ctx["val"], vexp, min_hist=min_hist)

        def rev(sr_vec, k):
            sl = slice(k * 24, k * 24 + 24)
            ac = row_ac(pdc[hh[sl]], sr_vec, cfg)
            return (ac * vfc[sl][None, :]).sum(1)

        R0 = np.zeros((n, HH)); sr = est.copy()
        for k in range(HH):
            R0[:, k] = rev(sr, k); sr = np.maximum(cfg["sr_floor"], sr - inc[d + k] * expo)
        Rr = np.zeros((H, HH))                   # reset at window day t, revenue on day k >= t (row-specific if expo)
        Rrow = np.zeros((n, H, HH)) if oracle_expo else None
        for t in range(H):
            sr = np.full(n, sc)
            for k in range(t, HH):
                r_k = rev(sr, k)
                if oracle_expo: Rrow[:, t, k] = r_k
                else: Rr[t, k] = r_k[0]
                sr = np.maximum(cfg["sr_floor"], sr - inc[d + k] * expo)
        def Rr_(i, t, a, b):
            return (Rrow[i, t, a:b] if oracle_expo else Rr[t, a:b]).sum()
        idx = {}; obj = []
        def add(key, c):
            idx[key] = len(obj); obj.append(c)
        for i in range(n):
            add((i, "S", "E"), -R0[i].sum())
            for t in range(H):
                add((i, "S", t), -R0[i, :t].sum())
                add((i, t, "E"), -Rr_(i, t, t, HH))
                for t2 in range(t + 1, H):
                    add((i, t, t2), -Rr_(i, t, t, t2))
        for t in range(H):
            for S in subs:
                add(("y", S, t), cfg["c_mission"] + cfg["c_row"] * len(S))
        N = len(obj); A = lil_matrix((n * (H + 2) + H * (n + 1), N)); r = 0; lo = []; hi = []
        for i in range(n):
            A[r, idx[(i, "S", "E")]] = 1
            for t in range(H): A[r, idx[(i, "S", t)]] = 1
            lo.append(1); hi.append(1); r += 1
            for t in range(H):
                A[r, idx[(i, "S", t)]] += 1
                for t0 in range(t): A[r, idx[(i, t0, t)]] += 1
                A[r, idx[(i, t, "E")]] -= 1
                for t2 in range(t + 1, H): A[r, idx[(i, t, t2)]] -= 1
                lo.append(0); hi.append(0); r += 1
        for t in range(H):
            for i in range(n):
                A[r, idx[(i, "S", t)]] += 1
                for t0 in range(t): A[r, idx[(i, t0, t)]] += 1
                for S in subs:
                    if i in S: A[r, idx[("y", S, t)]] -= 1
                lo.append(0); hi.append(0); r += 1
            for S in subs: A[r, idx[("y", S, t)]] = 1
            lo.append(0); hi.append(1); r += 1
        ub = np.ones(N)
        for t in range(H):
            for S in subs:
                if any(black[d + t, i] for i in S) or (t == 0 and not all(avail[i] for i in S)):
                    ub[idx[("y", S, t)]] = 0
        t0 = time.time()
        res = milp(c=np.array(obj), constraints=LinearConstraint(A[:r].tocsr(), lo, hi), integrality=np.ones(N),
                   bounds=Bounds(np.zeros(N), ub), options=dict(time_limit=time_limit, disp=False, mip_rel_gap=gap))
        rt = time.time() - t0
        if log is not None:
            log.append(dict(day=d, H=H, HH=HH, n_vars=N, status=int(res.status), runtime=rt,
                            mip_gap=None if res.mip_gap is None else float(res.mip_gap),
                            obj=None if res.x is None else float(res.fun),
                            bound=None if getattr(res, "mip_dual_bound", None) is None else float(res.mip_dual_bound),
                            has_solution=res.x is not None))
        if res.x is None:
            return []
        for S in subs:
            if res.x[idx[("y", S, 0)]] > 0.5:
                return list(S)
        return []
    return decide
