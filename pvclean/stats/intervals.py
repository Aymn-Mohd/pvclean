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


def cluster_spearman(x: Sequence[float], y: Sequence[float], cluster: Sequence[str], B: int = 2000, seed: int = 0) -> dict[str, Any]:
    """Spearman rho with a cluster bootstrap: whole clusters are drawn with replacement, B times, numpy default_rng(seed), percentile 95% interval. A resample with no variation in x or y has
    no rho; it is dropped and counted."""
    x = np.asarray(x, float); y = np.asarray(y, float); c = np.asarray(cluster)
    names = sorted(set(c.tolist())); idx = [np.flatnonzero(c == n) for n in names]
    rng = np.random.default_rng(seed); rhos = []; dropped = 0
    for _ in range(B):
        i = np.concatenate([idx[j] for j in rng.integers(0, len(names), len(names))])
        if np.ptp(x[i]) == 0 or np.ptp(y[i]) == 0:
            dropped += 1
            continue
        rhos.append(stats.spearmanr(x[i], y[i])[0])
    return dict(rho=float(stats.spearmanr(x, y)[0]), lo=float(np.percentile(rhos, 2.5)), hi=float(np.percentile(rhos, 97.5)), n=len(x), clusters=len(names), B=B, seed=seed, dropped=dropped)


def nested_bootstrap(D: Any, B: int = 2000, seed: int = 0) -> dict[str, Any]:
    """Interval of the mean of D[set, replicate]: draw the sets with replacement, then, inside each drawn set, draw the replicates with replacement. numpy default_rng(seed), percentile 95%."""
    D = np.asarray(D, float); S, R = D.shape
    rng = np.random.default_rng(seed); m = np.empty(B)
    for b in range(B):
        sets = rng.integers(0, S, S); reps = rng.integers(0, R, (S, R))
        m[b] = D[sets[:, None], reps].mean()
    return dict(mean=float(D.mean()), lo=float(np.percentile(m, 2.5)), hi=float(np.percentile(m, 97.5)), B=B, seed=seed, sets=S, replicates=R)
