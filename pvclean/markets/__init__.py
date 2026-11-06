"""Market registry and interval-level valuation. To add a market: one new file here and one line in REGISTRY, then set `market` in a study."""
from __future__ import annotations
from typing import Any
import numpy as np
from pvclean.contracts import get_contract
from .base import Market
from .generated import GeneratedMarket
from .real import RealMarket

REGISTRY: dict[str, Market] = {
    "generated": GeneratedMarket(),
    "SA1_aligned": RealMarket("SA1_aligned"),
    "SA1_raw": RealMarket("SA1_raw"),
    "QLD1_aligned": RealMarket("QLD1_aligned"),
    "QLD1_raw": RealMarket("QLD1_raw"),
    "ES_raw": RealMarket("ES_raw"),
    "ES_aligned": RealMarket("ES_aligned"),
}


def register(name: str, market: Market) -> None:
    """Adds a market at run time."""
    REGISTRY[name] = market


def get_market(name: str) -> Market:
    """The market called `name`."""
    return REGISTRY[name] if name in REGISTRY else RealMarket(name)


def spot_prices(seed: int, cfg: dict[str, Any]) -> np.ndarray:
    """Hourly spot prices [USD/kWh]: cfg real_market or cfg market names the source; the default is the generated market."""
    return get_market(cfg.get("real_market") or cfg.get("market") or "generated").spot(seed, cfg)


def contract_value(contract: str, seed: int, cfg: dict[str, Any], hourly_value: Any = None) -> tuple[np.ndarray, np.ndarray | None]:
    """Hourly contract value of one simulated year and the forecast warm-up. Interval-level values apply when cfg real_value is set and the contract has them."""
    c = get_contract(contract)
    if cfg.get("real_value") and c.interval_key:
        return get_market(cfg["real_value"]).interval_value(c, seed, cfg)
    spot = spot_prices(seed, cfg)
    return (hourly_value(contract, spot, cfg) if hourly_value else c.hourly_value(spot, cfg)), None
