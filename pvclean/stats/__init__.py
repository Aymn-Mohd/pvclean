"""Paired intervals, the quantity and timing decomposition, and the decision-rule evaluators."""
from .decomposition import decomp
from .intervals import ci95, paired, paired_short, paired_summary, spearman, year_stratified
from .rules import interval_rule, robust_rule, tally_rule

__all__ = ["ci95", "decomp", "interval_rule", "paired", "paired_short", "paired_summary", "robust_rule", "spearman", "tally_rule", "year_stratified"]
