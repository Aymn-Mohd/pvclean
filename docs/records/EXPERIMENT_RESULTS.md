# Experiment results (v10, 2026-10-11)

All numbers are read from `results/*.json`. Nothing was tuned on test seeds: heuristics and planners are tuned on
seeds 1000–1004 (synthetic) or training years (real-market), and evaluated on test seeds/years. Paired
differences report the mean and the 95 % bootstrap interval (`evaluation.paired_summary`; real-market:
`evaluation.year_stratified`, years fixed, replicates resampled within year). "ft" = forecast-matched price-aware
threshold baseline (V9_AUDIT A5).

## 1. Optimisation diagnostics (EXP-02 … 05)

See `docs/OPTIMISATION_DIAGNOSTICS.md`. Summary:
- Every MILP solve was optimal (`status 0`) with no constraint violations.
- Deterministic belief world, merchant / 12 USD/row, days 120–180: **H14 = 0 vs J* = 20.40; H30 = H60 = 20.40.**
  Across all 16 deterministic instances H60 and H30+T30 equal J*.
- Stochastic small instances, merchant/12: H14 1.97 → H14+T16 / H30 / H60 15.54 USD (+13.6 [7.4, 20.5]).
- The v9 "9 %" result is a horizon / terminal-value effect, not a MILP bug.
- All-oracle arm L7 = clairvoyant 7.37 USD on seed 0 (confirmed). Exact match on 18/20 seeds in merchant/12 and
  5/20 in fixed/4; it is never above the clairvoyant optimum, and the mean shortfall is −0.07 and −0.62 USD.

## 2. ft vs proposed on the small instances (matched_information part B; seeds 0–19)

| setting | ft | proposed | proposed − ft [95 % boot] | proposed wins |
|---|---|---|---|---|
| fixed / 4 | 146.9 ± 17.4 | 140.5 ± 19.7 | −6.4 [−9.6, −2.7] | 10 % |
| fixed / 12 | 79.1 ± 14.3 | 67.7 ± 13.8 | −11.4 [−21.7, −2.9] | 25 % |
| merchant / 4 | 60.2 ± 8.9 | 42.0 ± 10.7 | −18.2 [−22.8, −13.7] | 5 % |
| merchant / 12 | 3.7 ± 5.2 | 4.5 ± 8.8 | +0.8 [−5.9, 7.2] | 55 % |

(± is the t 95 % half-width.) **On the small instances ft beats the proposed planner in 3 of 4 settings, and
matches it (no significant difference) in merchant/12.** For comparison, the H30+T30 MILP in the same settings
reaches 147.4 / 81.4 / 62.9 / 15.5.

## 3. Generated markets, 40 rows, 50 test seeds (price_aware_baseline)

Mean incremental net value (USD) over no cleaning:

| contract | fixed | threshold | econ | ft | proposed | best baseline |
|---|---|---|---|---|---|---|
| fixed | 24 732.7 | 25 525.9 | 25 558.0 | 25 593.6 | **25 641.5** | econ |
| merchant | 15 383.8 | 15 961.0 | 15 923.5 | 15 992.8 | **16 117.9** | threshold |
| ppa | 18 932.2 | 19 520.0 | 19 426.9 | 19 535.5 | **19 590.2** | threshold |
| capped | 21 305.9 | 21 924.0 | 21 862.5 | **21 955.4** | 21 946.8 | threshold |

Paired differences:

| contract | proposed − best baseline | ft − best baseline | proposed − ft | proposed − econ |
|---|---|---|---|---|
| fixed | +83.5 [55.9, 112.3] | +35.6 [−2.6, 75.2] | +47.9 [12.2, 83.0] | +83.5 [55.9, 112.3] |
| merchant | +156.9 [118.0, 194.8] | +31.7 [−10.1, 73.8] | +125.2 [84.2, 168.1] | +194.4 [156.9, 232.4] |
| ppa | +70.2 [36.4, 103.0] | +15.5 [−17.8, 48.9] | +54.7 [16.5, 91.7] | +163.3 [126.7, 200.7] |
| capped | +22.8 [−3.3, 49.3] | +31.4 [11.6, 51.3] | **−8.6 [−29.5, 12.4]** | +84.3 [60.5, 107.7] |

- In fixed, merchant and ppa the proposed planner beats ft significantly. The margin over ft (48–125 USD) is
  smaller than the margin over econ (84–194 USD), so part of v9's gain over econ is explained by price awareness.
- **Capped: ft matches the proposed planner** (−8.6 [−29.5, 12.4]). Proposed is not significantly better than the
  best baseline there (+22.8 [−3.3, 49.3]); ft is (+31.4 [11.6, 51.3]).
- ft alone is not significantly better than the best baseline in fixed, merchant or ppa.

## 4. Real-market replay (SA1, QLD1, OMIE ES; 3 price-year folds × 50 weather/dust replicates)

Mean incremental net value over folds (USD). Best baseline = best of fixed/threshold/econ under F0.
Differences: year-stratified mean [95 % interval], years positive / years.

### Proposed − ft by forecast scenario

| market / contract | F0 clim | F1 prev-year | F2 rolling | F3 + operating day | F4 oracle |
|---|---|---|---|---|---|
| SA1 merchant | **−205 [−254, −156]** 0/3 | −140 [−180, −100] 0/2 | +124 [95, 154] 2/3 | +292 [270, 315] 3/3 | +86 [67, 106] 3/3 |
| SA1 PPA | −107 [−134, −80] 0/3 | −134 [−163, −104] 0/2 | +21 [3, 39] 2/3 | +88 [70, 105] 3/3 | +71 [50, 92] 3/3 |
| QLD1 merchant | **−655 [−699, −611]** 0/3 | −436 [−493, −379] 0/2 | +61 [39, 83] 1/3 | +189 [170, 208] 3/3 | +80 [58, 104] 3/3 |
| QLD1 PPA | −87 [−113, −61] 0/3 | −56 [−78, −32] 0/2 | +147 [124, 171] 3/3 | +73 [52, 95] 3/3 | +66 [47, 86] 3/3 |
| ES merchant | **−1 562 [−1 676, −1 457]** 0/3 | −354 [−401, −310] 0/2 | +166 [138, 193] 2/3 | +224 [201, 246] 3/3 | +187 [161, 213] 2/3 |
| ES PPA | −85 [−114, −57] 1/3 | +8 [−13, 29] 1/2 | +67 [47, 87] 3/3 | +80 [61, 99] 3/3 | +64 [44, 84] 3/3 |

### Proposed and ft vs best F0 baseline

| market / contract (best baseline) | proposed F0 | proposed F2 | proposed F3 | ft F0 | ft F2 | ft F3 |
|---|---|---|---|---|---|---|
| SA1 merchant (threshold) | −35 [−74, 6] | +79 [41, 117] | +450 [416, 484] | +170 [128, 212] | −45 [−82, −10] | +158 [126, 188] |
| SA1 PPA (econ) | −8 [−37, 22] | +80 [55, 105] | +199 [177, 221] | +99 [74, 124] | +59 [37, 82] | +111 [90, 133] |
| QLD1 merchant (threshold) | −670 [−720, −623] | +28 [1, 55] | +194 [169, 219] | −16 [−41, 9] | −33 [−58, −9] | +5 [−20, 29] |
| QLD1 PPA (threshold) | −57 [−83, −33] | +61 [37, 85] | +120 [97, 142] | +30 [7, 53] | −86 [−109, −64] | +46 [25, 67] |
| ES merchant (econ) | −1 938 [−2 076, −1 802] | +338 [308, 367] | +502 [478, 526] | −376 [−471, −289] | +172 [143, 201] | +278 [250, 307] |
| ES PPA (threshold) | −82 [−112, −52] | +53 [34, 73] | +81 [62, 101] | +3 [−13, 18] | −14 [−32, 4] | +1 [−16, 18] |

Findings (including negative results):
- **With climatological forecasts (F0, F1) the proposed planner loses to ft in every market/contract except
  ES PPA F1 (tie)**, and loses to the best simple baseline in 4 of 6 cases (significantly). The largest loss is
  ES merchant F0: −1 938 USD vs econ.
- With the causal rolling forecast (F2), proposed beats ft in all 6 cases (+21 … +166) and beats the best F0
  baseline in all 6 (+28 … +338).
- With F3 (operating-day prices; deployable only in Spain, an oracle for the NEM) proposed beats ft by +73 … +292
  and the best baseline by +81 … +502.
- ft does not benefit consistently from better forecasts: ft F2 is *below* the best baseline in SA1 merchant,
  QLD1 merchant and QLD1 PPA.
- The proposed planner cleans more than ft in most cells (e.g. SA1 merchant F0: 398 vs 312 cleanings); exceptions are QLD1 merchant F0/F1 and ES merchant F2/F3.

## 5. Forecast leakage audit (EXP-07)

23 562 poison checks, **0 failures** (same as the previous run). See `docs/FORECAST_LEAKAGE_AUDIT.md`.
