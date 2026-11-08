"""Paired intervals, the quantity and timing decomposition, and the decision-rule evaluators."""
from .decomposition import decomp
from .intervals import ci95, cluster_spearman, paired, paired_short, nested_bootstrap, paired_summary, spearman, year_stratified
from .rules import DRY_HIGH, DRY_LOW, HEADROOM_CUT, SHARE_TARGET, dry_prediction, dry_rule, ft_plain_rule, headroom_rule, interval_rule, robust_rule, tally_rule

__all__ = ["DRY_HIGH", "DRY_LOW", "HEADROOM_CUT", "SHARE_TARGET", "ft_plain_rule", "headroom_rule", "nested_bootstrap", "ci95", "cluster_spearman", "decomp", "dry_prediction", "dry_rule", "interval_rule", "paired", "paired_short", "paired_summary", "robust_rule", "spearman", "tally_rule", "year_stratified"]
