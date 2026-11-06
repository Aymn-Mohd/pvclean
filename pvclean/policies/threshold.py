"""Loss threshold."""
import numpy as np
from pvclean.core.robot import pack
from .base import Decision, Policy, State


class LossThreshold(Policy):
    """Cleans rows whose estimated loss reaches theta, dirtiest first."""
    name = "threshold"

    def decide(self, s: State) -> Decision:
        wanted = 1 - s.est >= self.params["theta"]
        due = np.where(wanted & s.avail)[0]
        due = due[np.argsort(s.est[due])]
        return Decision(pack(list(due), s.cfg), wanted, "soiling_threshold")
