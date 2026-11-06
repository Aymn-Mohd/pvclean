"""A new contract in one file: a higher tariff in the evening."""
import numpy as np
from pvclean.contracts.base import Contract


class TimeOfUse(Contract):
    name = "tou"

    def hourly_value(self, spot, cfg):
        return np.tile(np.where(np.arange(24) >= 17, 2 * cfg["tariff"], cfg["tariff"]), 365)
