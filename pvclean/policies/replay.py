"""Replay of a fixed schedule."""
from .base import Decision, Policy, State


class ScheduleReplay(Policy):
    """Runs params["sched"], {day: rows}, as given. It scores a schedule found elsewhere in the simulator's own ledger."""
    name = "replay"

    def decide(self, s: State) -> Decision:
        return Decision(self.params["sched"].get(s.d, ()))
