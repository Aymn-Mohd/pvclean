"""No cleaning."""
from .base import Decision, Policy, State


class NoCleaning(Policy):
    """Never cleans and never patrols. The reference for value of cleaning."""
    name = "none"
    inspects = False

    def decide(self, s: State) -> Decision:
        return Decision()
