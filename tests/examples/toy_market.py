"""A new price market in one file: a flat price."""
import numpy as np
from pvclean.markets.base import Market


class FlatMarket(Market):
    name = "flat"

    def spot(self, seed, cfg):
        return np.full(8760, 0.05)
