"""Sites: one YAML file each. To add a site: one new file here and one line in REGISTRY."""
from __future__ import annotations
import os
from typing import Any
from pvclean.config import load_yaml

HERE = os.path.dirname(os.path.abspath(__file__))
REGISTRY: dict[str, str] = {
    "dubai": os.path.join(HERE, "dubai.yaml"),
    "adelaide": os.path.join(HERE, "adelaide.yaml"),
    "brisbane": os.path.join(HERE, "brisbane.yaml"),
    "seville": os.path.join(HERE, "seville.yaml"),
    "almeria": os.path.join(HERE, "almeria.yaml"),
    "cordoba": os.path.join(HERE, "cordoba.yaml"),
    "bilbao": os.path.join(HERE, "bilbao.yaml"),
    "port_augusta": os.path.join(HERE, "port_augusta.yaml"),
    "longreach": os.path.join(HERE, "longreach.yaml"),
    "murcia": os.path.join(HERE, "murcia.yaml"),
    "badajoz": os.path.join(HERE, "badajoz.yaml"),
    "a_coruna": os.path.join(HERE, "a_coruna.yaml"),
    "whyalla": os.path.join(HERE, "whyalla.yaml"),
    "mount_gambier": os.path.join(HERE, "mount_gambier.yaml"),
    "roma_qld": os.path.join(HERE, "roma_qld.yaml"),
}


def register(name: str, path: str) -> None:
    """Adds a site file at run time."""
    REGISTRY[name] = path


def load_site(name: str) -> dict[str, Any]:
    """The contents of one site file."""
    return load_yaml(REGISTRY[name])


def site_params(name: str) -> dict[str, Any]:
    """Model parameters of any site: location, orientation, market and weather source. Merge them into a config or a study's `site:`."""
    s = load_site(name)
    out = {k: s[k] for k in ("lat", "lon", "tilt", "azimuth", "tz", "market", "weather_source")}
    if s["weather_source"] == "nasa_site":
        out.update(wx_site=s["name"], time_base=s["time_base"])
    return out


def site_config(name: str) -> dict[str, Any]:
    """The model parameters of a site with measured weather."""
    s = load_site(name)
    return dict(wx_site=s["name"], lat=s["lat"], lon=s["lon"], tilt=s["tilt"], azimuth=s["azimuth"], tz=s["tz"], time_base=s["time_base"])
