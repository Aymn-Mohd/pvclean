"""Policy registry. To add a policy: one new file here and one line in REGISTRY."""
from __future__ import annotations
from typing import Any, Type
from .base import Decision, Policy, State
from .economic import Economic
from .fixed_interval import FixedInterval
from .ft import ForecastThreshold
from .mpc import RecedingHorizon
from .none import NoCleaning
from .planner import Planner, PlannerNoBatching, PlannerNoValuation
from .replay import ScheduleReplay
from .threshold import LossThreshold

REGISTRY: dict[str, Type[Policy]] = {
    "none": NoCleaning,
    "fixed": FixedInterval,
    "threshold": LossThreshold,
    "econ": Economic,
    "ft": ForecastThreshold,
    "proposed": Planner,
    "proposed_noval": PlannerNoValuation,
    "proposed_nobatch": PlannerNoBatching,
    "mpc": RecedingHorizon,
    "replay": ScheduleReplay,
}


def register(name: str, policy: Type[Policy]) -> None:
    """Adds a policy at run time."""
    REGISTRY[name] = policy


def make_policy(name: str, params: dict[str, Any]) -> Policy:
    """A policy object with its parameters."""
    return REGISTRY[name](params)
