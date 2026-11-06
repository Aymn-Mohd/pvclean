"""Decision-rule evaluators. Each applies a pre-registered rule as written."""
from __future__ import annotations
from typing import Any, Iterable
import numpy as np


def tally_rule(rows: Iterable[dict[str, Any]], supported_at: int = 10, not_supported_at: int = 6) -> dict[str, Any]:
    """H-R1 and H-R3: SUPPORTED if the mean is above 0 in at least supported_at rows and no interval lies wholly below 0; NOT SUPPORTED if the mean is at or
    below 0 in at least not_supported_at rows; PARTIAL otherwise."""
    rows = list(rows)
    pos = sum(r["mean"] > 0 for r in rows); nonpos = len(rows) - pos; below = sum(r["hi"] < 0 for r in rows)
    if pos >= supported_at and below == 0:
        v = "SUPPORTED"
    elif nonpos >= not_supported_at:
        v = "NOT SUPPORTED"
    else:
        v = "PARTIAL"
    return dict(verdict=v, n=len(rows), mean_pos=pos, mean_nonpos=nonpos, ci_wholly_below=below, ci_wholly_above=sum(r["lo"] > 0 for r in rows))


def interval_rule(rows: Iterable[dict[str, Any]], supported_at: int = 6, not_supported_at: int = 6) -> dict[str, Any]:
    """H-R2: SUPPORTED if the interval lies wholly above 0 in at least supported_at cells and wholly below 0 in none; NOT SUPPORTED if the mean is at or below 0 in
    at least not_supported_at cells; PARTIAL otherwise."""
    v = list(rows)
    above = sum(x["lo"] > 0 for x in v); below = sum(x["hi"] < 0 for x in v); nonpos = sum(x["mean"] <= 0 for x in v)
    if above >= supported_at and below == 0:
        verdict = "SUPPORTED"
    elif nonpos >= not_supported_at:
        verdict = "NOT SUPPORTED"
    else:
        verdict = "PARTIAL"
    return dict(verdict=verdict, n=len(v), ci_wholly_above=above, ci_wholly_below=below, mean_nonpos=nonpos, mean_pos=len(v) - nonpos)


def robust_rule(default: dict[str, Any], var: dict[str, Any]) -> str:
    """R1b: ROBUST if the sign matches the default and, where the default interval excludes 0, the variant's interval is not wholly on the other side."""
    same_sign = np.sign(var["mean"]) == np.sign(default["mean"])
    if default["lo"] > 0:
        other_side = var["hi"] < 0
    elif default["hi"] < 0:
        other_side = var["lo"] > 0
    else:
        other_side = False
    return "ROBUST" if (same_sign and not other_side) else "NOT ROBUST"
