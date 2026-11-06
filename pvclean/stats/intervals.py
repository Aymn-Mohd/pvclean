"""Paired t intervals and bootstrap summaries at the right level of replication.

Generated markets: each seed is an independent draw. Real markets: only three price years exist, so intervals over replicates are conditional on those
years, and no population-level market claim follows. Exact instances: each seed is an independent instance.
"""
from __future__ import annotations
from typing import Any, Sequence
import numpy as np
from scipy import stats


def ci95(x: Sequence[float]) -> tuple[float, float]:
    """Mean and 95% t half-width. With one value the half-width is 0."""
    x = np.asarray(x, float)
    if len(x) < 2:
        return float(x.mean()), 0.0
    h = stats.t.ppf(0.975, len(x) - 1) * x.std(ddof=1) / np.sqrt(len(x))
    return float(x.mean()), float(h)


def paired(a: Sequence[float], b: Sequence[float]) -> dict[str, Any]:
    """Paired difference a - b: mean, interval and wins."""
    d = np.asarray(a, float) - np.asarray(b, float)
    m, h = ci95(d)
    return dict(mean=m, lo=m - h, hi=m + h, ci=h, wins=int((d > 0).sum()), n=len(d))


def paired_short(a: Sequence[float], b: Sequence[float]) -> dict[str, Any]:
    """Paired difference in the shorter record of the first generated-market studies: mean, half-width, wins."""
    d = np.array(a) - np.array(b)
    m, h = ci95(d)
    return dict(mean=m, ci=h, wins=int((d > 0).sum()), n=len(d))


def paired_summary(a: Sequence[float], b: Sequence[float] | None = None, n_boot: int = 10000, seed: int = 0) -> dict[str, Any]:
    """Mean, median, t interval, bootstrap interval, win share and standard deviation of a - b."""
    d = np.asarray(a, float) - (0.0 if b is None else np.asarray(b, float))
    n = len(d)
    mean = float(d.mean()); med = float(np.median(d))
    h = float(stats.t.ppf(0.975, n - 1) * d.std(ddof=1) / np.sqrt(n)) if n > 1 else 0.0
    rng = np.random.default_rng(seed)
    bs = d[rng.integers(0, n, (n_boot, n))].mean(1)
    return dict(n=n, mean=mean, median=med, t_ci=h, boot_lo=float(np.quantile(bs, .025)), boot_hi=float(np.quantile(bs, .975)),
                wins=float((d > 0).mean()), sd=float(d.std(ddof=1)) if n > 1 else 0.0)


def year_stratified(diffs_by_year: dict[Any, Sequence[float]], n_boot: int = 10000, seed: int = 0) -> dict[str, Any]:
    """Years are fixed strata: the bootstrap resamples replicates within each year, and the statistic is the mean of the within-year means."""
    rng = np.random.default_rng(seed)
    yrs = sorted(diffs_by_year)
    means = {y: float(np.mean(diffs_by_year[y])) for y in yrs}
    boots = np.zeros(n_boot)
    for y in yrs:
        d = np.asarray(diffs_by_year[y], float)
        boots += d[rng.integers(0, len(d), (n_boot, len(d)))].mean(1)
    boots /= len(yrs)
    return dict(per_year=means, mean=float(np.mean(list(means.values()))), lo=float(np.quantile(boots, .025)),
                hi=float(np.quantile(boots, .975)), years_positive=int(sum(m > 0 for m in means.values())), n_years=len(yrs),
                n_rep=int(sum(len(v) for v in diffs_by_year.values())), conditional_on_years=True)


def spearman(x: Sequence[float], y: Sequence[float]) -> tuple[float, float]:
    """Spearman rank correlation and p-value."""
    r, p = stats.spearmanr(x, y)
    return float(r), float(p)
