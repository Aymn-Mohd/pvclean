"""Model parameters and the tuning protocol, loaded from defaults.yaml and protocol.yaml."""
from __future__ import annotations
import itertools
import os
from dataclasses import dataclass, field
from typing import Any
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
TUPLE_KEYS = ("storm_loss", "mobile_measure_clip", "mobile_k_clip", "wx_haze_index", "wx_rain_index", "wx_index_clip", "wx_rain_gamma")
# The parameter set of the original CONFIG: the keys that results/results.json stores under "config".
STORED_CONFIG_KEYS = ("lat", "lon", "tz", "alt", "year", "tilt", "azimuth", "n_rows", "row_kwp", "dc_ac", "inv_eff", "gamma", "row_pitch_m", "soil_mean", "season_amp",
                      "daily_cv", "expo_front", "expo_back", "expo_sigma", "storm_rate", "storm_loss", "sr_floor", "price_depress_scale", "rain_full_mm", "rain_full_recov",
                      "rain_light_mm", "rain_light_recov", "clean_residual", "c_row", "c_mission", "c_insp", "patrol_every", "night_min", "service_min", "speed_mps", "blackouts",
                      "tariff", "ppa", "export_cap_frac", "horizon_days", "rain_fc_days", "rain_fc_hit", "rain_fc_false")


def load_yaml(path: str) -> dict[str, Any]:
    """Reads one YAML file into a dict."""
    with open(path) as f:
        return yaml.safe_load(f)


def load_defaults() -> dict[str, Any]:
    """The default parameter dict. Pairs that the model unpacks are tuples."""
    cfg = load_yaml(os.path.join(HERE, "defaults.yaml"))
    for k in TUPLE_KEYS:
        cfg[k] = tuple(cfg[k])
    cfg["blackouts"] = tuple(tuple(b) for b in cfg["blackouts"])
    return cfg


CONFIG: dict[str, Any] = load_defaults()


def merged(over: dict[str, Any] | None = None) -> dict[str, Any]:
    """A copy of the defaults with `over` applied."""
    cfg = dict(CONFIG)
    cfg.update(over or {})
    return cfg


def seeds(spec: Any) -> list[int]:
    """A seed list from a YAML value: a list, or {start, stop}."""
    return list(range(spec["start"], spec["stop"])) if isinstance(spec, dict) else list(spec)


def grid(spec: dict[str, list]) -> list[dict[str, Any]]:
    """All parameter combinations of one grid, first key outermost, as the original comprehensions ordered them."""
    keys = list(spec)
    return [dict(zip(keys, v)) for v in itertools.product(*(spec[k] for k in keys))]


@dataclass
class Protocol:
    """Seeds and grids of one study. Passed explicitly, so a study cannot change another's settings."""
    train: list[int]
    test: list[int]
    grids: dict[str, list[dict[str, Any]]]
    contracts: list[str]
    baselines: list[str]
    workers: int = field(default_factory=lambda: os.cpu_count() or 1)

    def with_(self, **kw: Any) -> "Protocol":
        """A copy with some fields replaced."""
        return Protocol(**{**self.__dict__, **kw})


def load_protocol(over: dict[str, Any] | None = None) -> Protocol:
    """The default protocol with a study's `protocol:` section applied. A grid in `over` replaces that policy's grid only."""
    p = load_yaml(os.path.join(HERE, "protocol.yaml"))
    over = dict(over or {})
    p["grids"].update(over.pop("grids", {}))
    p.update(over)
    return Protocol(train=seeds(p["train_seeds"]), test=seeds(p["test_seeds"]), contracts=list(p["contracts"]), baselines=list(p["baselines"]),
                    grids={k: grid(v) for k, v in p["grids"].items()}, workers=p.get("workers", os.cpu_count() or 1))
