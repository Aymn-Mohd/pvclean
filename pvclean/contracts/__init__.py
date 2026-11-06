"""Contract registry. To add a contract: one new file here and one line in REGISTRY."""
from __future__ import annotations
from typing import Any
import numpy as np
from .base import Contract
from .export_cap import ExportCap
from .fixed import FixedTariff
from .merchant import Merchant
from .ppa import PPA

REGISTRY: dict[str, Contract] = {
    "fixed": FixedTariff(),
    "merchant": Merchant(),
    "ppa": PPA(),
    "capped": ExportCap(),
}


def register(name: str, contract: Contract) -> None:
    """Adds a contract at run time."""
    REGISTRY[name] = contract


def get_contract(name: str) -> Contract:
    """The contract called `name`."""
    if name not in REGISTRY:
        raise ValueError(name)
    return REGISTRY[name]


def hourly_value(contract: str, spot: np.ndarray, cfg: dict[str, Any]) -> np.ndarray:
    """Marginal revenue per delivered kWh in each hour under a contract."""
    return get_contract(contract).hourly_value(spot, cfg)
