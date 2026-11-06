"""Economic baseline at a constant price."""
import numpy as np
from pvclean.core.robot import pack
from .base import Decision, State
from .renewal import RenewalIndex


class Economic(RenewalIndex):
    """Renewal index at the constant price, with the mission cost shared over b rows."""
    name = "econ"

    def decide(self, s: State) -> Decision:
        phi, _ = self.index(s)
        phi = phi - s.cfg["c_mission"] / self.params["b"]
        wanted = phi >= 0
        due = np.where(wanted & s.avail)[0]
        due = due[np.argsort(-phi[due])]
        return Decision(pack(list(due), s.cfg), wanted, "renewal_index")
