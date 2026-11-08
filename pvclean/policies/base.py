"""Policy interface and the per-year state a policy reads."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any
import numpy as np
from pvclean.core.plant import row_ac
from pvclean.forecasts import day_types, fc_value


@dataclass
class Decision:
    """Tonight's rows. `wanted` marks rows the policy would take if none were closed (mission log only); `reason` labels the mission."""
    rows: Any = ()
    wanted: np.ndarray | None = None
    reason: str | None = None


class State:
    """What a policy may read on day d. The simulator owns it. Arrays est, tau, A and last_clean are the live state of the year."""
    cfg: dict[str, Any]
    d: int
    n: int
    avail: np.ndarray        # rows open tonight
    black: np.ndarray        # (365, n) closed rows
    est: np.ndarray          # estimated soiling ratio
    tau: np.ndarray          # days since last cleaning (robot or full rain)
    A: np.ndarray            # accumulated estimated lost value since last cleaning
    last_clean: np.ndarray
    fc: np.ndarray           # daily rain forecast flags
    clim: np.ndarray
    vexp: np.ndarray
    pbar: float
    val: np.ndarray
    warm: np.ndarray | None
    pdc: np.ndarray
    capped: bool
    lim: float
    sr_clean: float
    H: int                   # planning horizon [hours]
    wrap: bool
    dg: dict[str, Any] | None   # diagnostics of this day, None when off
    expo: np.ndarray         # true values, for oracle arms of the receding-horizon optimiser only
    inc: np.ndarray
    rain: np.ndarray
    row_noise: np.ndarray
    seed: int                # the run's seed; picks the price year, for calendar-only inputs such as day_types()

    def rain_soon(self) -> bool:
        """Is full-cleaning rain forecast within the rain forecast window?"""
        return self.fc[self.d:self.d + self.cfg["rain_fc_days"]].any()

    def gain(self, profile: np.ndarray) -> np.ndarray:
        """Extra delivered energy per row and hour if the row were clean, on a production profile; includes the export limit."""
        ac_now = row_ac(profile, self.est, self.cfg)
        ac_cl = row_ac(profile, np.full(self.n, self.sr_clean), self.cfg)
        if self.capped:
            plant = ac_now.sum(0)
            return np.minimum(self.lim, plant[None, :] - ac_now + ac_cl) - np.minimum(self.lim, plant)[None, :]
        return ac_cl - ac_now

    def forecast(self, hh: np.ndarray) -> np.ndarray:
        """Value forecast of cfg fc_mode for hours hh."""
        cfg = self.cfg; mode = cfg.get("fc_mode", "clim"); dt = None
        if mode == "roll_hw":
            if getattr(self, "_day_type", None) is None:
                self._day_type = day_types(cfg, self.seed)
            dt = self._day_type
        return fc_value(mode, self.d, hh, self.val, self.vexp, cfg.get("roll_min_hist", cfg["roll_min_hist_default"]), self.warm, roll_days=cfg["roll_days"], day_type=dt)

    def closing_soon(self) -> tuple[np.ndarray, np.ndarray] | None:
        """Days each open row will be closed in the look-ahead window, for rows that close tomorrow; None if no open row closes tomorrow."""
        soon = self.black[min(self.d + 1, 364)] & self.avail
        if not soon.any():
            return None
        return self.black[self.d + 1:self.d + 1 + self.cfg["access_lookahead_days"]].sum(0), soon


class Policy:
    """A cleaning policy. `params` holds its tuned parameters. A new policy implements decide(); book() runs after each day's production."""
    name = ""
    inspects = True     # mobile information patrols apply to this policy

    def __init__(self, params: dict[str, Any]) -> None:
        self.params = params

    def decide(self, s: State) -> Decision:
        """Tonight's cleaning on day s.d."""
        raise NotImplementedError

    def book(self, s: State, hs: slice) -> None:
        """Updates policy state from the realised day. The default does nothing."""
