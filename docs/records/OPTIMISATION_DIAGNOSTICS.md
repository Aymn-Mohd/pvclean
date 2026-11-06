# Optimisation diagnostics (EXP-02 … EXP-05)

Sources: `results/results_horizon.json` (680 runs), `results/results_matched.json` (`part_a`),
`results/check_L7_vs_clairvoyant.json`. All runs from 2026-10-11 (see `docs/REPRODUCIBILITY.md`).
Small instances: 6 rows, `night_min=100`, days 120–180 unless stated. Gains are USD over the no-cleaning schedule.

## Question

v9 reported that the receding-horizon ("matched") MILP recovered only ~9 % of the clairvoyant gain in the
merchant / 12 USD-per-row setting (V9_AUDIT A2). Is that a MILP/solver bug, or a horizon/terminal-value effect?

## Solver health

| Check | Result |
|---|---|
| Horizon study solves (680 runs, 1 084 solves per setting arm) | every solve `status = 0` (optimal); no run without a solution |
| Largest reported MIP gap in any horizon solve | 0.0010 (tolerance `gap=1e-3`) |
| Schedule-constraint violations (`checks.schedule_violations`) | 0 in all 680 runs, all 16 Part A J* schedules and all Part A MPC arms |
| Part A full-horizon J* solves (16) | all `status = 0`, MIP gap 0.0 |
| Clairvoyant solves for the L7 check (40) | all `status = 0`, max gap 9.9e-5 |
| Longest single MPC solve | 18.7 s (H60, merchant/12); all others ≤ 4.3 s (limit 60 s) |

No solve hit the time limit, so time limits do not explain any result below.

## Part A — deterministic belief world (truth = planner's belief)

Here the world is the planner's own model (expected dust, no rain, equal exposure, climatological production,
expected prices) and the state is known. The full-horizon certified MILP gives J*. Any MPC shortfall below J*
can only come from the horizon / terminal value. One instance per setting and window (seed 0).

**Key finding — confirmed.** Merchant, 12 USD/row, days 120–180: J* = **20.40**. H07 = 0, **H14 = 0** (never
cleans), H30 = H60 = H14+T16 = H30+T30 = **20.40**, i.e. exactly J*.

Full table (gain, USD):

| contract | c_row | d0 | J* | H07 | H14 | H30 | H60 | H14+T16 | H30+T30 |
|---|---|---|---|---|---|---|---|---|---|
| fixed | 4 | 60 | 103.84 | 88.44 | 103.23 | 98.44 | 103.84 | 98.44 | 103.84 |
| fixed | 4 | 120 | 162.27 | 140.78 | 154.43 | 161.42 | 162.27 | 160.57 | 162.27 |
| fixed | 4 | 180 | 152.41 | 135.02 | 147.57 | 142.21 | 152.41 | 142.21 | 152.41 |
| fixed | 4 | 240 | 88.14 | 41.35 | 81.32 | 87.81 | 88.14 | 87.81 | 88.14 |
| fixed | 12 | 60 | 50.44 | 0.00 | 34.48 | 50.44 | 50.44 | 50.44 | 50.44 |
| fixed | 12 | 120 | 94.92 | 0.00 | 92.52 | 94.92 | 94.92 | 94.92 | 94.92 |
| fixed | 12 | 180 | 89.27 | 0.00 | 85.47 | 88.67 | 89.27 | 88.67 | 89.27 |
| fixed | 12 | 240 | 40.14 | 0.00 | 0.00 | 39.81 | 40.14 | 39.81 | 40.14 |
| merchant | 4 | 60 | 0.00 | 0 | 0 | 0 | 0 | 0 | 0 |
| merchant | 4 | 120 | 68.40 | 17.52 | 67.62 | 68.40 | 68.40 | 68.40 | 68.40 |
| merchant | 4 | 180 | 114.86 | 95.07 | 114.86 | 109.45 | 114.86 | 109.45 | 114.86 |
| merchant | 4 | 240 | 39.99 | 0.00 | 33.51 | 39.32 | 39.99 | 39.32 | 39.99 |
| merchant | 12 | 60 | 0.00 | 0 | 0 | 0 | 0 | 0 | 0 |
| **merchant** | **12** | **120** | **20.40** | 0.00 | **0.00** | **20.40** | **20.40** | 20.40 | 20.40 |
| merchant | 12 | 180 | 61.68 | 0.00 | 43.71 | 61.45 | 61.68 | 61.45 | 61.68 |
| merchant | 12 | 240 | 0.00 | 0 | 0 | 0 | 0 | 0 | 0 |

Observations:
- **H60 and H30+T30 equal J* in all 16 instances.** No MPC arm ever exceeds J*. This is consistent with a correct
  MILP formulation: given enough look-ahead, the receding-horizon solution reproduces the certified optimum.
- H30 and H14+T16 are not always optimal (e.g. fixed/4/d0=180: 142.21 vs 152.41). The shortfall goes away at H60
  or H30+T30, so it is an end-of-horizon effect.
- H07 is poor everywhere. At 12 USD/row it never cleans in 7 of 8 instances.
- In the three instances with J* = 0, tuned `threshold`, `econ` and `proposed` *lose* money (down to −71.7 USD)
  even though they are tuned in this same world; `fixed` and `ft` keep 0.

Tuned heuristics in the same world (they are tuned in the belief world, which favours them):
merchant/12/d0=120 — fixed 8.69, threshold 16.94, econ 16.94, **proposed 20.40**, ft 18.57. Over all 16
instances, `proposed` reaches J* only in that instance and in merchant/12/d0=180.

## Horizon and terminal value on the stochastic small instances (EXP-03/04)

Truth = full stochastic simulator, seeds 0–19, site information. Mean gain ± s.e., and paired difference vs H14
(the v9 arm) with a 95 % bootstrap interval.

| setting | H07 | H14 (v9) | H14+T16 | H30 | H30+T30 | H60 |
|---|---|---|---|---|---|---|
| fixed / 4 | 127.33 | 141.82 | 144.57 | 145.86 | 147.38 | – |
| fixed / 12 | 2.44 | 75.67 | 81.69 | 81.73 | 81.36 | – |
| merchant / 4 | 14.14 | 61.96 | 63.15 | 63.14 | 62.93 | – |
| merchant / 12 | 0.00 | **1.97** | 15.54 | 15.53 | 15.54 | 15.54 |

Paired differences vs H14:
- merchant / 12: H14+T16 +13.57 [7.37, 20.52]; H30 +13.56 [7.37, 20.52]; H30+T30 +13.57 [7.55, 20.34];
  H60 +13.57 [7.55, 20.34]. Mean cleanings rise from 0.3 (H14) to 4.8.
- fixed / 12: H30 +6.06 [3.13, 9.23]; fixed / 4: H30+T30 +5.56 [1.77, 9.44]; merchant / 4: H30 +1.19 [0.22, 2.28].
- H07 is significantly worse than H14 in every setting (e.g. fixed/12 −73.23).

H14 = 1.97 USD in merchant/12 reproduces the v9 figure (1.97 USD, 0.3 cleanings; V9_AUDIT A2). A 16-day terminal
tail on a 14-day horizon (H14+T16) is enough to remove the effect; extending to 60 days adds nothing.

**Conclusion:** the v9 "9 %" result is a horizon / terminal-value effect, not a MILP bug. With a 14-day horizon
and no terminal value, a 12 USD/row clean does not pay back inside the horizon, so the MPC never cleans.

## Information ladder (EXP-05; all at H30+T30)

Each rung adds information to the matched arm (L0 = H30+T30). Mean gain; paired difference vs H14 in brackets.

| rung | fixed / 4 | merchant / 12 |
|---|---|---|
| L0 matched (= H30+T30) | 147.38 | 15.54 |
| L1 + row exposure | 145.63 | 13.76 |
| L2 + next-24 h prices | – | **0.00** |
| L3 + all prices | 147.38 | 15.80 |
| L4 + future dust | 152.30 | 17.09 |
| L5 + future weather | 147.09 | 14.99 |
| L6 + true row state | 147.97 | 19.59 |
| L7 all of L1–L6 | 153.59 | 21.51 |

- Future dust (L4) and the true row state (L6) are the most valuable single items. Prices (L3) add almost nothing
  in fixed/4 (identical to L0) and +0.26 in merchant/12.
- L1 (exposure) and L5 (weather) are slightly *below* L0 in both settings (paired L1−L0 / L5−L0 differences were
  not separately tested; the size, 0.3–1.8 USD, is small relative to seed-to-seed s.e. of 3–8 USD).
- **L2 anomaly (null/negative result).** L2 never cleans (0.00 on all 20 seeds, same as H07). `price_mode="dayahead"`
  is not "L0 + 24 h of prices": in `forecasting.value_forecast`, `dayahead` replaces the climatological expected
  price beyond the first 24 h with a causal rolling 28-day profile (the F2 forecast) as well. L2 therefore changes
  two things at once, and the rung is not a clean single-item step. The mechanism that makes the rolling-profile
  forecast suppress all cleaning here was not investigated further; it is reported as observed.

## All-oracle arm vs clairvoyant optimum

The L7 arm (H30+T30 with all oracle information and true state) was compared seed-by-seed with the clairvoyant
optimum from `exact.solve` on the same instances (`results/check_L7_vs_clairvoyant.json`; script in
`docs/EXPERIMENT_LOG.md`).

| setting | clairvoyant mean | L7 − clairvoyant: mean | worst | seeds with exact match (abs. diff < 0.01) |
|---|---|---|---|---|
| merchant / 12 | 21.58 | −0.071 | −1.076 (seed 13) | 18 / 20 |
| fixed / 4 | 154.21 | −0.624 | −3.024 (seed 18) | 5 / 20 |

- **Seed 0, merchant / 12: L7 = clairvoyant = 7.37 USD — confirmed.**
- The claim does not generalise to "exactly reproduces the optimum" across seeds. L7 is never above the
  clairvoyant value (as it must be). It is within 0.4 % on average in fixed/4 and matches on 18/20 seeds in
  merchant/12. The remaining shortfall is consistent with the 30+30-day receding horizon, not with the clairvoyant
  model having the full 60-day window.
