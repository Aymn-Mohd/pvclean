"""A deterministic world in which the truth equals the information-matched planner's model: expected dust increment, no rain, equal row exposure, climatological production and
expected hourly value. Used to isolate optimisation quality, because everything except the decision rule is held fixed."""
from __future__ import annotations
import numpy as np
from pvclean.core.soiling import expected_increment
from pvclean.core.world import World


def belief_world(clim: np.ndarray, vexp: np.ndarray) -> World:
    """The World of one planner belief."""
    return World(weather=lambda seed, cfg: dict(pdc=clim, rain=np.zeros(365), clear_pdc=None),
                 dust=lambda seed, cfg: (expected_increment(cfg), np.ones((365, cfg["n_rows"]))),
                 exposure=lambda cfg, site_seed=None, hetero=1.0: np.ones(cfg["n_rows"]),
                 hourly_value=lambda contract, spot, cfg: vexp,
                 rain_forecast=lambda rain, seed, cfg: np.zeros(365, bool))
