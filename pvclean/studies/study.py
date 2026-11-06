"""A study: one YAML file that names a runner, its output file, its protocol and its parameters."""
from __future__ import annotations
import json
import os
from dataclasses import dataclass, field
from typing import Any
from pvclean.config import Protocol, load_protocol, load_yaml
from pvclean.data import repo_root, results_dir
from .runner import Runner


@dataclass
class Study:
    """Loaded study config. `out_dir` receives the output; `stored()` reads results of earlier studies from the stored results."""
    name: str
    runner: str
    output: str
    params: dict[str, Any]
    protocol: Protocol
    out_dir: str
    label: str = ""
    extra_outputs: list[str] = field(default_factory=list)

    def runner_pool(self) -> Runner:
        """A Runner on a new pool."""
        return Runner(self.protocol)

    def stored(self, name: str) -> Any:
        """A stored result file, as parsed JSON."""
        return json.load(open(self.stored_path(name)))

    def stored_path(self, name: str) -> str:
        """Path of a stored result."""
        return os.path.join(results_dir(), name)

    def out_path(self, name: str | None = None) -> str:
        """Path in the output directory, which is created if needed."""
        os.makedirs(self.out_dir, exist_ok=True)
        return os.path.join(self.out_dir, name or self.output)

    def write(self, data: Any, name: str | None = None) -> str:
        """Writes JSON to the output directory, atomically."""
        path = self.out_path(name)
        with open(path + ".part", "w") as f:
            json.dump(data, f, indent=1, default=float)
        os.replace(path + ".part", path)
        return path


def default_out_dir(name: str) -> str:
    """New runs go to runs/<study>/, never over stored results unless asked."""
    return os.path.join(repo_root(), "runs", name)


def load_study(path: str, out_dir: str | None = None, workers: int | None = None) -> Study:
    """Reads a study YAML."""
    y = load_yaml(path)
    p = load_protocol(y.get("protocol"))
    if workers:
        p = p.with_(workers=workers)
    return Study(name=y["study"], runner=y["runner"], output=y["output"], params=y.get("params") or {}, protocol=p, out_dir=out_dir or default_out_dir(y["study"]), label=y.get("label", ""))
