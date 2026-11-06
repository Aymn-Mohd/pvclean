"""The planner and its two ablations."""
from __future__ import annotations
import numpy as np
from pvclean.core.robot import pack
from .base import Decision, State
from .renewal import RenewalIndex


class Planner(RenewalIndex):
    """Contract-aware renewal index with access anticipation and mission batching. A mission goes out when the excess index pays kappa missions; rows within beta row
    costs of the index join it."""
    name = "proposed"
    contract_aware = True

    def anticipate(self, s: State, phi: np.ndarray, g: np.ndarray) -> np.ndarray:
        """A row closed for L days soon pays L days of loss."""
        c = s.closing_soon()
        if c is None:
            return phi
        L, soon = c
        return phi + np.where(soon, g * L, 0.0)

    def decide(self, s: State) -> Decision:
        phi_plain, g = self.index(s)
        phi = self.anticipate(s, phi_plain, g)
        rain_soon = s.rain_soon()
        if s.dg is not None:
            s.dg.update(phi=phi.copy(), A=s.A.copy(), g=g.copy(), rain_soon=bool(rain_soon))
        return self.choose(s, phi, phi_plain, rain_soon)

    def choose(self, s: State, phi: np.ndarray, phi_plain: np.ndarray, rain_soon: bool) -> Decision:
        cfg, avail, kappa = s.cfg, s.avail, self.params["kappa"]
        ready = (phi >= 0) & avail
        excess = np.maximum(phi, 0)[avail].sum()
        if not (ready.any() and excess >= cfg["c_mission"] * kappa and not rain_soon):
            return Decision()
        wanted = phi >= -self.params["beta"] * cfg["c_row"]
        cand = np.where(wanted & avail)[0]
        cand = cand[np.argsort(-phi[cand])]
        plain = ((phi_plain >= 0) & avail).any() and np.maximum(phi_plain, 0)[avail].sum() >= cfg["c_mission"] * kappa
        return Decision(pack(list(cand), cfg), wanted, "batched_index" if plain else "access_anticipation")


class PlannerNoValuation(Planner):
    """Ablation: the planner at the constant price."""
    name = "proposed_noval"
    contract_aware = False


class PlannerNoBatching(Planner):
    """Ablation: the planner without mission batching; the mission cost is shared over b rows."""
    name = "proposed_nobatch"

    def choose(self, s: State, phi: np.ndarray, phi_plain: np.ndarray, rain_soon: bool) -> Decision:
        cfg, avail = s.cfg, s.avail
        share = cfg["c_mission"] / self.params.get("b", 4)
        phi_b = phi - share
        wanted = phi_b >= 0
        due = np.where(wanted & avail)[0]
        due = due[np.argsort(-phi_b[due])]
        rows = [] if rain_soon else pack(list(due), cfg)
        return Decision(rows, wanted, "renewal_index" if ((phi_plain - share >= 0) & avail).any() else "access_anticipation")
