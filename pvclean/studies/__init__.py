"""Study runners. To add a runner: a function taking a Study, and one line in RUNNERS."""
from __future__ import annotations
import importlib
import time
from typing import Any
from .study import Study, load_study

# runner name -> module:function. Modules load on first use, so a run imports only what it needs.
RUNNERS: dict[str, str] = {
    "quickstart": "generated:quickstart", "generated": "generated:rq", "ft_synthetic": "generated:ft_synthetic", "extra": "generated:extra", "nrel": "generated:nrel", "wx": "generated:wx",
    "real": "hourly:real", "roll": "hourly:roll", "oracle": "hourly:oracle", "spain": "hourly:spain", "forecast": "hourly:forecast", "replay": "hourly:replay",
    "chrono": "chrono:chrono", "rq1_decomp": "chrono:rq1_decomposition",
    "matched": "matched:r3", "site_weather": "matched:site_weather", "kappa": "matched:kappa", "gauge_rain": "matched:gauge_rain",
    "robot_sweep": "robot_sweep:run", "robustness": "robustness:run",
    "exact": "exact_bench:exact", "exact_matched": "exact_bench:exact_matched", "mpc": "exact_bench:mpc", "horizon": "horizon:run", "belief_benchmark": "belief_benchmark:run",
    "milp_gaps": "milp_gaps:run", "forecast_audit": "forecast_audit:run", "price_audit": "price_audit:run", "sanity_tau": "sanity_tau:run", "claims_recheck": "claims_recheck:run",
    "failure_diag": "failure_diag:run", "mission_trace": "mission_trace:run", "r2_checks": "r2_checks:run", "r3_checks": "r3_checks:run", "audit_counts": "audit_counts:run",
}


def runner_function(name: str) -> Any:
    """The function behind a runner name."""
    mod, fn = RUNNERS[name].split(":")
    return getattr(importlib.import_module(f"pvclean.studies.{mod}"), fn)


def run_study(path: str, out_dir: str | None = None, workers: int | None = None) -> tuple[str, float]:
    """Runs one study YAML and writes its output. Returns (output path, seconds)."""
    S = load_study(path, out_dir, workers)
    t0 = time.time()
    result = runner_function(S.runner)(S)
    return S.write(result), time.time() - t0


__all__ = ["RUNNERS", "Study", "load_study", "run_study", "runner_function"]
