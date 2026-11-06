"""Receding-horizon optimiser supplied by the caller (pvclean.exact)."""
from .base import Decision, Policy, State


class RecedingHorizon(Policy):
    """params["fn"] decides; the rain gate applies as for the planner."""
    name = "mpc"

    def decide(self, s: State) -> Decision:
        if s.rain_soon():
            return Decision()
        ctx = dict(val=s.val, expo=s.expo, inc=s.inc, rain=s.rain, pdc=s.pdc, rowsoil=s.row_noise, tau=s.tau.copy(), A=s.A.copy(), black=s.black)
        return Decision(self.params["fn"](s.d, s.est.copy(), s.avail, s.cfg, s.clim, s.vexp, ctx))
