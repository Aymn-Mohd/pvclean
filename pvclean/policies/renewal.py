"""Renewal index shared by the economic baseline and the planner: phi = g tau - A - c_row, with g the expected value lost per day."""
from __future__ import annotations
import numpy as np
from .base import Policy, State


class RenewalIndex(Policy):
    """contract_aware policies value the loss under the contract and the forecast; the others use the constant price pbar."""
    contract_aware = False

    def index(self, s: State) -> tuple[np.ndarray, np.ndarray]:
        """Returns (phi, g)."""
        cfg, d = s.cfg, s.d
        hh = np.arange(d * 24, d * 24 + s.H) % 8760 if s.wrap else np.arange(d * 24, min(d * 24 + s.H, 8760))
        ndays = len(hh) / 24.0
        if self.contract_aware:
            gain = s.gain(s.clim[hh])
            vf = s.forecast(hh)
            g = (gain * vf[None, :]).sum(1) / ndays
            if s.dg is not None:
                s.dg["vhat"] = float(vf.mean())
        else:
            e_h = cfg["row_kwp"] * s.clim[hh] * cfg["inv_eff"]
            g = s.pbar * np.outer(s.sr_clean - s.est, e_h).sum(1) / ndays
        return g * s.tau - s.A - cfg["c_row"], g

    def book(self, s: State, hs: slice) -> None:
        """Books the estimated lost value of the day; realised prices are known after the day."""
        if self.contract_aware:
            s.A += (s.gain(s.pdc[hs]) * s.val[hs][None, :]).sum(1)
        else:
            cfg = s.cfg
            s.A += s.pbar * (s.sr_clean - s.est) * cfg["row_kwp"] * cfg["inv_eff"] * s.pdc[hs].sum()
