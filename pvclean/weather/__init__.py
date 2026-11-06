"""Weather sources and their registry. To add a source: one new file here and one line in REGISTRY, then set `weather_source` in a site or study."""
from __future__ import annotations
from typing import Any, Callable
from .generated import weather_generated
from .nasa_dubai import weather_dubai
from .nasa_site import SITE_COLS, site_table, site_year, to_time_base, weather_site

REGISTRY: dict[str, Callable[[int, dict[str, Any]], dict[str, Any]]] = {
    "generated": weather_generated,
    "nasa_dubai": weather_dubai,
    "nasa_site": weather_site,
}


def register(name: str, source: Callable[[int, dict[str, Any]], dict[str, Any]]) -> None:
    """Adds a weather source at run time."""
    REGISTRY[name] = source


def source_of(cfg: dict[str, Any]) -> str:
    """The weather source a config selects."""
    if cfg.get("weather_source"):
        return cfg["weather_source"]
    if cfg.get("wx_site"):
        return "nasa_site"
    if cfg.get("wx_years"):
        return "nasa_dubai"
    return "generated"


def weather(seed: int, cfg: dict[str, Any]) -> dict[str, Any]:
    """Hourly DC power per kWp and daily rain [mm] of one simulated year."""
    return REGISTRY[source_of(cfg)](seed, cfg)
