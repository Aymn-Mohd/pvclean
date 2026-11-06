"""A new policy in one file: clean the dirtiest open row every week."""
import numpy as np
from pvclean.policies import Decision, Policy, State


class WeeklyDirtiest(Policy):
    name = "weekly_dirtiest"

    def decide(self, s: State) -> Decision:
        if s.d % self.params.get("every", 7):
            return Decision()
        open_rows = np.where(s.avail)[0]
        return Decision([int(open_rows[np.argmin(s.est[open_rows])])], reason="weekly")
