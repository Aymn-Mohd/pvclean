"""Fixed interval."""
import numpy as np
from pvclean.core.robot import pack
from .base import Decision, Policy, State


class FixedInterval(Policy):
    """Cleans a row every T days, oldest first."""
    name = "fixed"

    def decide(self, s: State) -> Decision:
        wanted = s.d - s.last_clean >= self.params["T"]
        due = np.where(wanted & s.avail)[0]
        due = due[np.argsort(s.last_clean[due])]
        return Decision(pack(list(due), s.cfg), wanted, "interval_due")
