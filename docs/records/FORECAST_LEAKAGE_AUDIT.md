# Forecast leakage audit (EXP-07)

Source: `results/results_forecast_audit.json`, produced by `experiments/forecast_audit.py` (rerun 2026-10-11).

## Method

For every market (SA1, QLD1, OMIE ES), contract (merchant, PPA), price year (fold 0–2), causal scenario
(F0 climatology, F1 previous-year climatology, F2 rolling 28-day, F3 rolling + operating-day prices) and decision
day d = 1…357, the 168-hour value forecast is recomputed with every realised value at or after
`forecasting.info_cutoff(mode, d)` set to NaN. The forecast must be finite and identical to the unpoisoned
forecast. F4 (oracle) is excluded by design; it is not deployable.

## Result

| | |
|---|---|
| checks | **23 562** |
| failures | **0** |

This matches the earlier run (23 562 checks, 0 failures). No causal scenario reads a value it is not entitled
to see at the decision time.

Caveat that this audit does **not** cover (see `docs/LIMITATIONS.md` item 4): F0 climatology and the tuning step
use other years in a leave-one-year-out scheme, so for early folds they use *later* years. That is acausal across
years even though it passes the within-year cutoff check. F3 is a published day-ahead product only for Spain; for
SA1/QLD1 it is a "next-24-hours-known" oracle (V9_AUDIT A3).

## Forecast error (contract value, USD/kWh; 168 h horizon, daylight hours; mean over folds)

| market | contract | F0 MAE | F1 MAE | F2 MAE | F3 MAE | F0 bias | F1 bias |
|---|---|---|---|---|---|---|---|
| SA1 | merchant | 0.0377 | 0.0404 | 0.0402 | 0.0346 | +0.0011 | +0.0057 |
| SA1 | PPA | 0.0192 | 0.0189 | 0.0194 | 0.0167 | +0.0001 | +0.0017 |
| QLD1 | merchant | 0.0277 | 0.0320 | 0.0274 | 0.0237 | +0.0007 | +0.0058 |
| QLD1 | PPA | 0.0156 | 0.0153 | 0.0150 | 0.0129 | +0.0001 | +0.0033 |
| ES | merchant | 0.0409 | 0.0412 | 0.0299 | 0.0258 | +0.0002 | +0.0176 |
| ES | PPA | 0.0059 | 0.0053 | 0.0042 | 0.0036 | −0.0000 | +0.0035 |

F4 has zero error by construction. F1 is available for folds 1–2 only.

- F3 has the lowest MAE everywhere, as expected.
- In the NEM, the causal rolling forecast (F2) is no better than climatology (SA1 merchant: F2 0.0402 vs F0 0.0377).
  In Spain, F2 is clearly better (merchant 0.0299 vs 0.0409).
- F1 (previous year only) has a consistent positive bias, largest in Spain merchant (+0.0176 USD/kWh).
- RMSE in SA1 merchant is 0.13–0.14 USD/kWh, against an MAE of about 0.04: errors are dominated by price spikes.

The run emits `RuntimeWarning: Mean of empty slice` for market/year cells with no negative-price daylight hours.
In those cells `mae_neg_hours` is NaN, and this has no effect on the other metrics.
