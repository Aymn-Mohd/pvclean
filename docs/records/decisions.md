# Decisions

Blockers and decisions from the `pvclean` restructure, 2026-11-05.

## Folded from other branches

From `GPU_HOST-runs`: `CLAUDE.md` (rewritten for the new layout), and this log line, kept here so that `EXPERIMENT_LOG.md` stays word for word:

> - 2026-10-16 (ANALYSIS, not pre-registered): horizon file check of `results/results_horizon.json` (sha256 329c702d…783a): 680 records, 0 duplicate keys, all 36 856 solves status 0; recomputed H-arm mean gains vs docs/OPTIMISATION_DIAGNOSTICS.md → MATCH (max |diff| 0.0049). Blockers: a working-practice document missing (copied from HOME_DIR/Desktop/icmre-sensing/docs, matches the pasted text); `src/make_outputs_v10.py` missing (means computed directly). See docs/HORIZON_FILE_CHECK.md.

From `e1-overlap-cleanup`, the log note only:

> ## EXP-08 scope decision
>
> EXP-08 moved to a separate paper on 13 Oct 2026. E1 does not report it. The simulator description stays.

That branch's code change is not folded in. It deletes paper macros such as `InspWeekly`, which would break byte-identical output. The paper sources decide this, not the restructure.

## Definition of "the same"

Stored results are not overwritten. New code must match the archived code rerun on this machine, bit for bit. Paper macros must stay byte-identical. Some stored files differ from that rerun: see `docs/REVIEW.md` section 6.

## Blockers

- `real_prices.npz` cannot be rebuilt. See `docs/DATA.md`.
- `new/omie.csv`, `new/nasa_dubai.csv.gz` and the NLR files have no fetch script.

## Wording

Repo text describes the package by what it does, and says nothing about its ambitions. Five single words and one two-word phrase from the restructure brief are not used: they are in that brief, and `tests/test_repo_rules.py` holds the list. Records in this directory are exempt because they are kept word for word.

## Public release brief, 2026-11-06

The brief for the public release was cut off in the middle of Part B step 2, after "the results/*.json the paper macros need,". The rest of the keep list and any later steps did not arrive. Creating the public repository was refused by the session's permission check, so `GH_USER/pvclean` does not exist yet. The export was staged locally and nothing was published.

Update, 2026-11-06: `GH_USER/pvclean` was created, public and empty, after the owner allowed it. Nothing has been pushed to it. The rest of the brief is still missing.

2026-11-06: public release v1.0.0 pushed to Aymn-Mohd/pvclean (commit 85ea272); v1.0.1 fixes listed in CHANGELOG.md.

---
## Phase R4 (2026-11-07), PRE-REGISTERED before any R4 simulation
Question: does the longest dry spell, measured from rain alone, predict the sign of planner minus FT at new sites?
Runs: the 5 new sites (Almeria, Cordoba, Bilbao, Port Augusta, Longreach) x {merchant, PPA} x {2024, 2025} = 20 case-years. Everything else identical to R3: F2 forecast, soiling 0.30%/day, the same dust model and calendar, tune on 2023 then test 2024, tune on 2023 to 2024 then test 2025, 50 replicates, and the same grids including kappa in {0, 0.5, 1, 2}.
Prediction rule (from R3; Australia at most 67 days, Seville at least 179 days):
- longest dry spell >= 120 days: predict mean planner - FT > 0;
- <= 70 days: predict mean <= 0 (an exact tie counts as <= 0);
- otherwise no prediction.

Predicted sign of every new case-year, from results/r4_rain.json (commit 94389da). Each row covers both contracts.

| site | prices | year | longest dry spell (days) | rain (mm) | days >= 5 mm | days >= 1 mm | prediction |
|---|---|---|---|---|---|---|---|
| Almeria | ES_raw | 2024 | 195 | 219 | 13 | 54 | mean planner - FT > 0 |
| Almeria | ES_raw | 2025 | 238 | 269 | 13 | 64 | mean planner - FT > 0 |
| Cordoba | ES_raw | 2024 | 158 | 529 | 31 | 65 | mean planner - FT > 0 |
| Cordoba | ES_raw | 2025 | 119 | 703 | 42 | 90 | no prediction |
| Bilbao | ES_raw | 2024 | 24 | 1247 | 72 | 168 | mean planner - FT <= 0 |
| Bilbao | ES_raw | 2025 | 38 | 943 | 56 | 161 | mean planner - FT <= 0 |
| Port Augusta | SA1_raw | 2024 | 197 | 173 | 10 | 42 | mean planner - FT > 0 |
| Port Augusta | SA1_raw | 2025 | 158 | 119 | 4 | 36 | mean planner - FT > 0 |
| Longreach | QLD1_raw | 2024 | 230 | 236 | 11 | 34 | mean planner - FT > 0 |
| Longreach | QLD1_raw | 2025 | 138 | 276 | 12 | 32 | mean planner - FT > 0 |

Case-years predicted above 0: 14. Predicted at or below 0: 4. No prediction: 2.
Decision rule, over predicted case-years only:
- SUPPORTED if at least 80% have the predicted sign and each predicted side has at least 4 case-years;
- NOT SUPPORTED if 60% or fewer have the predicted sign;
- PARTIAL otherwise;
- DESCRIPTIVE if either side has fewer than 4 case-years.

Secondary, descriptive:
- Spearman rho between longest dry spell and mean planner - FT over all 32 case-years (12 R3 + 20 new), with a cluster bootstrap by site (B = 2000, numpy default_rng(0), percentile 95% CI);
- the same rho with soiling loss without cleaning in place of the dry spell;
- the within-Spain contrast (Bilbao, Cordoba, Almeria, Seville: same prices, different weather).

Report per case-year: soiling loss without cleaning (against a dust-free run), the planner's and FT's value of cleaning, rows cleaned by each, and the timing and quantity split.
Checks after the test, labelled POST HOC: wider kappa grid, shifted dust season, low soiling rate, cost sensitivity, tuning seeds.

### R4 implementation notes, fixed before any simulation
1. Rule order: DESCRIPTIVE is tested first, because it means the test has too few case-years on a side. With the table above both sides have at least 4, so it cannot apply, and the order does not matter unless a site is lost.
2. The at-or-below-0 side has exactly 4 case-years, all from Bilbao. It is one site. Its result is one site's result, and the verdict is read with that in mind. The above-0 side has 14 case-years from 4 sites. With 18 predicted case-years, SUPPORTED needs at least 15 correct and NOT SUPPORTED means 10 or fewer.
3. Cordoba 2025 has a 119-day spell, one day under the threshold. It gets no prediction. The thresholds are not moved. The two case-years stay in the secondary analyses.
4. Years downloaded: 2001 to 2025 for each new site, not only 2023 to 2025. R3's production climatology uses 2001 to the year before the test year, and pvclean.weather.build.read_power reads those years. 125 files, one request each, all HTTP 200.
5. Forecasts: F2 only. The record schema is that of results_matched.json, with keys soil0.30|site|contract|fold under `r4` and `r4_meta`, because three new sites share ES_raw. Records also hold `site`.
6. R3 values come from stored files, not reruns: results_matched.json (planner minus FT), results_r3b_rain.json (dry spell), r3_checks.json (soiling loss). The stored R3 shift check must equal the R3 rows of r4_shift.
7. Soiling loss: the method of r3_checks.part_soil: `none` policy, merchant, 50 test seeds, against soil_mean = 0 and storm_rate = 0.
8. Bootstrap: draw 8 sites with replacement; a resample with no variation in x or y is dropped and counted. The 32 case-years hold 16 site-years, because merchant and PPA share weather.
9. Dust season peak, storm timing and blackout days are unchanged at every site, as in R3 note 8. This includes the southern sites.
10. r4_shift: 182 days, as in R3, at 0.30%/day only. r4_lowsoil: only soil_mean changes, as in R3 note 7. r4_cost: c_row and c_mission scaled together, x0.5 and x2, c_insp unchanged; every policy retuned. r4_seeds: train seeds 1005-1009, 1010-1014, 1015-1019, as R3. r4_kappa: kappa grid {0, 0.5, 1, 2, 4, 8, 16, 32}, beta grid unchanged, as R3.
11. Figure, Dubai marker: mean longest dry spell of the generated weather (r3_checks.json r1wx); planner minus FT over the 12 R1 case-years on the same price series as R3 and R4 (SA1_raw, QLD1_raw, ES_raw). The value on R1's aligned Australian series is stated beside it.
12. Script paths follow the brief: src/make_r4_summary.py, src/make_fig_r4.py, docs/R4_SUMMARY.md, paper/.
13. NASA POWER rain is not checked against gauges at any site (R3b could not obtain gauge data). The dry spell here is the model's rain input, and the test is of that input.
---

### R4 results (2026-11-07)
- **R4 verdict: PARTIAL.** 13 of 18 predicted case-years have the predicted sign (72%). Predicted above 0: 14. Predicted at or below 0: 4. No prediction: 2.
- **Spearman rho over 32 case-years (DESCRIPTIVE):** dry spell +0.45 [-0.01, +0.69]; soiling loss without cleaning +0.53 [+0.19, +0.71]. Cluster bootstrap by site, 8 sites.
Tables, checks and sanity results: docs/R4_SUMMARY.md. Deviations: docs/records/EXPERIMENT_LOG.md, "Phase R4 run log".

---
## Phase R5 (2026-11-07), PRE-REGISTERED before any R5 simulation
Question: for MERCHANT contracts only, does the R4 rule predict the sign of planner - FT at unseen sites (>= 120 days: > 0; <= 70 days: <= 0; otherwise no prediction)?
Runs: 6 sites (Murcia, Badajoz, A Coruna, Whyalla, Mount Gambier, Roma) x merchant x {2024, 2025} = 12 case-years, R3/R4 settings: F2 forecast, soiling 0.30%/day, the same dust model and calendar, tune on 2023 then test 2024, tune on 2023 to 2024 then test 2025, 50 replicates, the same grids with kappa in {0, 0.5, 1, 2}.

Predicted sign of every merchant case-year, from results/r5_rain.json (commit 2721808). The same signs apply to the PPA rows, which are DESCRIPTIVE.

| site | prices | year | longest dry spell (days) | rain (mm) | days >= 5 mm | days >= 1 mm | prediction |
|---|---|---|---|---|---|---|---|
| Murcia | ES_raw | 2024 | 120 | 207 | 11 | 41 | mean planner - FT > 0 |
| Murcia | ES_raw | 2025 | 128 | 422 | 24 | 55 | mean planner - FT > 0 |
| Badajoz | ES_raw | 2024 | 98 | 563 | 40 | 76 | no prediction |
| Badajoz | ES_raw | 2025 | 146 | 770 | 51 | 110 | mean planner - FT > 0 |
| A Coruna | ES_raw | 2024 | 40 | 1276 | 82 | 155 | mean planner - FT <= 0 |
| A Coruna | ES_raw | 2025 | 64 | 1151 | 80 | 153 | mean planner - FT <= 0 |
| Whyalla | SA1_raw | 2024 | 135 | 183 | 12 | 42 | mean planner - FT > 0 |
| Whyalla | SA1_raw | 2025 | 158 | 145 | 4 | 41 | mean planner - FT > 0 |
| Mount Gambier | SA1_raw | 2024 | 90 | 508 | 28 | 103 | no prediction |
| Mount Gambier | SA1_raw | 2025 | 69 | 602 | 36 | 118 | mean planner - FT <= 0 |
| Roma | QLD1_raw | 2024 | 62 | 529 | 28 | 69 | mean planner - FT <= 0 |
| Roma | QLD1_raw | 2025 | 70 | 290 | 20 | 48 | mean planner - FT <= 0 |

Merchant case-years predicted above 0: 5. Predicted at or below 0: 5. No prediction: 2.
Decision rule: the same as R4, over predicted case-years only:
- SUPPORTED if at least 80% have the predicted sign and each predicted side has at least 4 case-years;
- NOT SUPPORTED if 60% or fewer have the predicted sign;
- PARTIAL otherwise;
- DESCRIPTIVE if either side has fewer than 4 case-years.

Secondary, DESCRIPTIVE: the same 6 sites under the PPA (12 case-years), and the R4 rule applied to all 24.
POST HOC: the wider kappa grid {0, 0.5, 1, 2, 4, 8, 16, 32} on all 24.

### R5 implementation notes, fixed before any simulation
1. With 10 predicted case-years, SUPPORTED needs at least 8 correct, PARTIAL is exactly 7, and NOT SUPPORTED is 6 or fewer. Both sides have 5, so DESCRIPTIVE cannot apply unless a site is lost. As in R4, DESCRIPTIVE is tested first.
2. Threshold cases: Murcia 2024 is exactly 120 days and Roma 2025 exactly 70. The rule is >= 120 and <= 70, so both are predicted. Mount Gambier 2025 (69) is one day inside the band edge. The thresholds are not moved.
3. Whyalla is not independent of R4. Its daily rain correlates 0.95 (2024) and 0.96 (2025) with Port Augusta, an R4 site, and the 2025 spell is 158 days at both. Port Augusta's merchant results were seen before this entry. The verdict uses all sites, as the brief says. The summary also reports the count without Whyalla, labelled DESCRIPTIVE. Other nearest-site correlations of daily rain: Badajoz and Seville 0.63, 0.72; Mount Gambier and Adelaide 0.40, 0.58; Murcia and Almeria 0.42, 0.38; A Coruna and Bilbao 0.35, 0.23; Roma and Brisbane 0.30, 0.12.
4. Why this is a fresh test: the merchant restriction came from R4's POST HOC table, so R4 cannot confirm it. R5 is the first test of it on sites chosen after that table. The thresholds still come from R3.
5. Known from R4 and kept as it is: on the kappa grid {0, 0.5, 1, 2}, Bilbao's losses came largely from the grid limit (R4 POST HOC). The main test uses that grid, as the brief says. An at-or-below-0 side that passes here may have the same cause; r5_kappa shows this.
6. Years downloaded: 2001 to 2025 for each new site, as in R4. 150 files, one request each, all HTTP 200. site_wx.npz was rebuilt; the 8 earlier site tables are bit-identical.
7. Schema: results_r5_merchant.json and results_r5_ppa.json use keys soil0.30|site|contract|fold under `r5` and `r5_meta`, as R4. Soiling loss and every other detail follow R4 implementation notes 5, 7 and 9.
8. Regression tests for R5 simulate, so they are held out of git and out of every test run until this entry is pushed.
9. NASA POWER rain is not checked against gauges at any site, as in R4 note 13.
---

### R5 results (2026-11-07)
- **R5 verdict: NOT SUPPORTED.** 5 of 10 = 50.0% with the predicted sign; predicted above 0: 5; predicted at or below 0: 5; no prediction: 2.
- **PPA (DESCRIPTIVE):** 6 of 10 = 60.0% with the predicted sign; predicted above 0: 5; predicted at or below 0: 5; no prediction: 2. The rule would say NOT SUPPORTED; this is not a verdict.
- **All 24 (DESCRIPTIVE):** 11 of 20 = 55.0% with the predicted sign; predicted above 0: 10; predicted at or below 0: 10; no prediction: 4. The rule would say NOT SUPPORTED; this is not a verdict.
Tables and checks: docs/R5_SUMMARY.md. Deviations: docs/records/EXPERIMENT_LOG.md, "Phase R5 run log".

---
## Phase R6 (2026-11-07), PRE-REGISTERED before any R6 run
Set: all 56 matched-site case-years (R3, R4 and R5 sites: 14 sites; merchant and PPA; 2024 and 2025), with F2 and the R3 settings.
H-R6a (headroom), MAIN: in case-years where the oracle's value of cleaning is at least 1,000 USD/yr, FT captures at least 90% of the oracle value.
- SUPPORTED if this holds in at least 80% of those case-years;
- NOT SUPPORTED if it holds in 60% or fewer;
- PARTIAL otherwise.
- Also report the planner's share of the oracle value, and both shares for case-years below 1,000 USD/yr (DESCRIPTIVE).

H-R6b (value of price-awareness), MAIN: under the merchant contract, FT outperforms the plain loss-threshold rule (no price forecast, tuned on the same years), over the merchant case-years where FT's value of cleaning is at least 1,000 USD/yr.
- SUPPORTED if the mean of FT minus plain threshold is positive in at least 80% of them and no interval lies wholly below 0;
- NOT SUPPORTED if the mean is at or below 0 in at least 50% of them;
- PARTIAL otherwise.
- PPA: the same comparison as DESCRIPTIVE.

DESCRIPTIVE, tuning-inclusive intervals: for planner minus FT in all 56 case-years, combine the 50 test replicates with 4 tuning-seed sets (the main set + 3) by nested bootstrap: resample seed sets, then replicates; B = 2000, numpy default_rng(0), percentile 95%. Report how many intervals lie wholly above 0, wholly below 0, or span 0, against the main intervals.

### R6 implementation notes, fixed before any R6 run
1. Oracle method. The subset MILP (pvclean/exact/milp.py) cannot reach a plant-year: one night has about 1e10 feasible row sets at 40 rows and 360 minutes. pvclean/exact/oracle.py (commit 0c34b63) keeps the same per-row path model. It returns a feasible schedule, by local search over mission nights with exact per-row dynamic programmes inside, and a Lagrangian upper bound. The true optimum lies between them. It equals the subset MILP exactly on 4 of its small instances (6 rows, 60 days), with the bound closed.
2. Constraints. The feasible schedule enforces everything, with no relaxation: known prices, rain, dust, row noise and exposure; night budget (mission_time, 360 min); access windows; c_row and c_mission per mission; robot availability 1.0. Only the upper bound relaxes the night budget, to the largest row count any night can hold. Each schedule is checked with schedule_violations and replayed through the simulator by the new  policy, so its value comes from the simulator's own ledger.
3. Oracle value of a case-year: mean over seeds of (feasible schedule net minus no cleaning). This is a lower bound on the true oracle value, so FT's share can be overstated by at most the bound gap. Verdict uses the feasible value. The summary also reports each share against the upper bound and what the rule would say on it, DESCRIPTIVE. Share = mean policy value / mean oracle value. A share with oracle value at or below 0 is undefined and dropped from medians.
4. Timing: 3 full units took 8, 46 and 58 s on one core, so at most about 1.9 h for 2,800 units on 24 workers. Under the 6 h limit, so all 50 seeds are used and no seed reduction applies. Those 3 timing units (Almeria merchant 2024 seed 0, Bilbao PPA 2024 seed 3, Seville merchant 2025 seed 7) were seen before this entry. For Almeria seed 0 the feasible value is 8769, FT's is 8195 (stored), and the path tables equal the simulator to rounding.
5. H-R6b is not a clean test of price alone. FT differs from the plain threshold in more than its price forecast: it also has a forward-looking net benefit rule with costs, the rain gate, the production climatology and access anticipation. A positive result says "FT beats the plain threshold", and does not isolate price. No price-blind FT arm is in this phase.
6. H-R6b is not blind. FT and plain-threshold test nets for all 56 case-years have been in stored results since R3 to R5, and R3 summary tables printed some related values. I have not computed FT minus plain for this phase, and will not until this entry is pushed. The FT-value selection (>= 1,000 USD/yr) is also known in advance from stored values. H-R6a has no such problem, because oracle values do not exist yet.
7. Plain threshold: the stored `threshold` baseline is that rule, tuned on the same years. r6_plain tunes it again for all 56 and must match the stored parameters and test nets exactly.
8. Seeds. The brief says R4 already has the 3 extra sets, but results_r4_seeds.json keeps summaries only, and the nested bootstrap needs per-replicate differences. r6_seeds therefore runs all 56 case-years, with train seeds 1005-1009, 1010-1014 and 1015-1019, keeps per-replicate differences, and must match the stored R3 and R4 means. The main set comes from the stored records.
9. Nested bootstrap: per case-year, a fresh numpy default_rng(0); draw 4 sets with replacement; inside each drawn set, draw 50 replicates with replacement, independently of the other drawn sets; statistic = mean of all drawn values. The 4 sets share their 50 test seeds, and 4 sets is few, so this interval is descriptive. The main interval is the paired t-interval.
10. Oracle below a policy. If a tuned policy beats the feasible oracle schedule at a seed, that is a search shortfall, not a bug: that seed is solved again from the policy's mission nights, and the count is reported. An upper bound below any policy would be a bug. Policies compared: fixed, threshold, econ, FT, planner.
11. Sanity triggers, per case-year means, as the brief lists: oracle below any policy; FT below plain threshold by more than 500 USD/yr; FT share above 100%. Each gets a same-seed rerun, identical inputs and a trace overlay, labelled REAL EFFECT or BUG.
12. The oracle knows true row exposure, dust and rain, while FT and the planner have station information and a rain forecast. Headroom therefore includes the value of that information as well as of better decisions.
13. The R6 regression tests run R6 jobs, so they are held out of git and of test runs until this entry is pushed.
---

---
## Phase R6 results (2026-11-08)
Rules applied as written by src/make_r6_summary.py; numbers from docs/R6_SUMMARY.md.
- **H-R6a: NOT SUPPORTED.** FT reaches 90% of the oracle value in 16 of 30 case-years at or above 1,000 USD/yr (53.3%; the rule's line is 60% or fewer). FT share median 90.6%, range 56.9% to 98.2%; planner share median 92.1%, range 55.9% to 98.5%, also 16 of 30 at target (DESCRIPTIVE). Against the upper bound: 15 of 30 (DESCRIPTIVE).
- **H-R6b: NOT SUPPORTED.** FT minus plain threshold is positive in 7 of 14 merchant case-years with FT value at or above 1,000 USD/yr, and at or below 0 in 7 (50%, the rule's line); 7 intervals lie wholly below 0. Median +66 USD/yr. PPA (DESCRIPTIVE): 6 of 12 positive, 4 wholly below 0, median +2.
- **Tuning-inclusive intervals (DESCRIPTIVE):** 22 above 0, 25 below 0, 9 span 0, against 20, 25 and 11 for the main intervals; 10 of 56 change side.
- One oracle fix after the run (BUG in the re-solve step, 24 units below the cut, no verdict changed): docs/records/EXPERIMENT_LOG.md, "Phase R6 run log", item 2.

---
## Phase R7 (sensitivity, specified before the runs), 2026-11-08
Requested by reviewers. Every output is SENSITIVITY: there are no hypotheses and no decision rules, and no result is a verdict. Tools: commit 426446e. No R7 job has run before this entry.
Set: the 56 matched-site case-years of R6 (14 sites x merchant, PPA x 2024, 2025), with the R3 settings unless a variant says otherwise. Policies reported: FT, planner and the plain loss threshold (`threshold`). In every variant all policies are retuned on the training years only, with chrono.run_fold, 5 train seeds (1000-1004), 50 test seeds (0-49). "Value" = mean over the test seeds of net minus no cleaning. Paired intervals are the t-intervals over the 50 test seeds, as in R3 to R6.
Qualifying case-years (used where stated): the 30 with R6 oracle value >= 1,000 USD/yr in results/results_r6_oracle.json. They lie at 8 sites.

### a) r7_forecast
Forecasts of the contract value, all causal except F4:
- F2: 28-day rolling hour-of-day mean (fc_mode roll, roll_days 28), as in R3 to R6.
- F7d: the same with roll_days 7. F56d: roll_days 56. The price file has 28 warm-up days, so for days 0-27 of a year F56d averages over the 28 + d days that exist; it never reads a later day.
- FHW: 28-day rolling hour-of-day mean taken separately over past weekdays and past weekend days (Saturday, Sunday), matched to the target day's type (pvclean/forecasts/roll_hw.py). Day types come from the price file's local timestamps. No public holidays.
- F3: the existing day-ahead mode: F2 plus the operating day's values. For ES these are day-ahead prices; for SA and QLD, the operating day's realised prices (a proxy: no day-ahead market).
- F4: the existing perfect mode: realised values over the planning window. Labelled INFORMATION UPPER BOUND, not deployable.
The plain threshold reads no prices, so it is retuned in each arm and must come out identical in all six; this is checked. The F2 arm must reproduce the stored R3 to R5 F2 nets of FT, planner and threshold exactly; this is checked.
Outputs per forecast: FT minus plain (value of price information), planner minus FT (value of planner design); for each, over the 56: count with mean > 0, count with the interval wholly above 0 and wholly below 0. Over the 30 qualifying: median, IQR (25th and 75th percentiles, numpy default) and range of the per-case-year mean FT minus plain, in USD/yr, and a cluster bootstrap 95% interval of that median: draw the 8 sites with replacement, pool their qualifying case-years, take the median; B = 2000, numpy default_rng(0), percentiles 2.5 and 97.5.

### b) r7_abstain
F2. Planner grid beta {0, 0.5, 1.0} x kappa {0, 0.5, 1, 2, 4, 8, 16, 32, inf}. kappa = inf means no mission is ever sent (excess >= c_mission x inf never holds). Other policies keep their grids. Outputs: planner minus FT sign counts over the 56 as in a), against the stored R3 to R5 counts; the four Brisbane rows; how many case-years tune to kappa = inf.

### c) r7_dust
F2. soil_mean 0.0010, 0.0015 and 0.0050 per day (0.0030 is the stored baseline). Outputs: sign counts as in a) for planner minus FT and for FT minus plain; median over the 56 of the share of each policy's value against the plain policy's value (FT / plain and planner / plain; plain / plain is 1 by definition). A case-year with plain value <= 0 has no share; it is dropped from that median and counted.

### d) r7_rain
F2. One setting at a time: rain_full_recov (>= 5 mm) 0.7 and 1.0 (0.9 now); rain_light_recov (1 to 5 mm) 0.1 and 0.3 (0.2 now). The policies' estimates use the same effectiveness as the plant. rain_reset_recov stays 0.9, so at rain_full_recov 0.7 a full rain no longer resets the policies' day and loss counters; at 1.0 it does, as now. Outputs as c).

### e) r7_cost
F2. c_row (4 USD) and c_mission (10 USD) scaled together by 0.5 and 2. Outputs as c).

### f) r7_oracle_split
The 30 qualifying case-years and the first 10 test seeds (0-9) only, to bound runtime. Each oracle is an open-loop plan for the whole year, solved by pvclean/exact/oracle.py (solve_oracle, as in R6, with no policy schedule as a start) on path tables built from the stated information, then scored in the simulator with the truth.
- C: the stored R6 oracle on seeds 0-9 (perfect prices, rain, dust and per-row soiling). Not rerun.
- A: true prices; rain known only through the policies' rain forecast flags (pvclean.core.soiling.rain_forecast, hit rate 0.8, false-alarm rate 0.05, for rain >= 5 mm): a flagged day is planned as rain_full_mm, every other day as dry. Closest valid variant, not the brief's exact definition: an open-loop plan cannot use the 2-day window, so A sees all flags of the year at once (more lead time than a policy), but never observes realised rain or light rain (less than a policy, whose estimate is corrected by realised rain each day). A can therefore fall below a policy; such cases are reported, not treated as bugs.
- B: F2 prices, perfect rain: every hour of day d is planned at the F2 value issued at the start of day d (the 28-day hour-of-day mean of the days before d), the same value a policy's F2 forecast gives for day d on night d.
- D: perfect prices and rain, but each row soils as the policies' station estimate assumes: the true site increment with exposure 1 + station_bias (= 1) and no row noise. This answers the question whether the oracle uses per-row true soiling: R6 and C do (true per-row exposure and daily row noise).
Outputs per oracle: value; FT, planner and plain shares = mean policy value over seeds 0-9 / mean oracle value over seeds 0-9 (policy nets from the stored R3 to R5 F2 records); median and range over the 30; and each oracle's value against C.
Prices and soiling cannot be separated further inside one open-loop plan; the oracle has no separate input for the 2-day rain window.

### Figure, sanity checks and outputs
src/make_r7_summary.py writes docs/R7_SUMMARY.md, labelled SENSITIVITY, every number generated. src/make_fig_r7.py writes paper/fig_policies.pdf (vector, 3.5 in, two stacked panels: (a) share of the R6 oracle value for FT, planner and plain in the 30 qualifying case-years, by oracle value on a log axis, with a dashed 90% line; (b) planner minus FT and FT minus plain, USD/yr, all 56, F2, strip plot over a box, zero line) and a 200 dpi PNG. No clipping: any value outside the default axis extends it, and the summary says so.
Sanity triggers: C below a policy at any seed (a bug); F4 FT value below F2 FT value by more than 500 USD/yr (case-year mean). Each gets a same-seed rerun, an identical-inputs check and a trace, and is labelled REAL EFFECT or BUG.

### Seen before this entry
During development: single simulations (FT, planner, fixed parameters, Seville merchant 2024, seed 0) under roll, roll_hw, dayahead, perfect and roll_days 7 and 56, to check that each mode runs; and three oracle-split timing units on Seville merchant 2024 seed 0: A 10,418, B 10,460, D 10,601 USD/yr against C 10,597, 23 to 116 s each. For that unit D's planned value equals its true value to 0.12 USD: when most rows are cleaned on the same nights, the plant total is nearly linear in mean exposure, which is 1, and the station belief costs almost nothing.
Release audit: docs/R7_RELEASE_AUDIT.md (written before any run; changes nothing public).
---

## Index of phases R3 to R7 (added for release 1.4.1)
Where each phase's definitions and rules were written before its runs, and the commits that registered and reported it. Commit hashes refer to the private development repository from which each release is exported; the public releases are listed last. The R3 and R3b pre-registrations were kept in the experiment log, the later ones in this file.

| phase | definitions, written before the runs | registered | results |
|---|---|---|---|
| R3 matched sites | `docs/records/EXPERIMENT_LOG.md`, "Phase R3 (2026-11-05), PRE-REGISTERED before any R3 run" | ab9dfdb (2026-11-05) | d69f238 (replay), a0ec103 (summary); POST HOC wider kappa grid: note 61a4ad3, run ab4c5ac |
| R3b gauge rain | `docs/records/EXPERIMENT_LOG.md`, "Phase R3b (2026-11-05), PRE-REGISTERED before any R3b run" | 2421d93 (2026-11-05) | c69283b, 51464a0, 7008040 (rule not evaluable: gauge downloads blocked) |
| R4 new sites, dry-spell rule | this file, "Phase R4 (2026-11-07), PRE-REGISTERED before any R4 simulation" | 177ff66 (2026-11-07) | 11a209c (2026-11-07) |
| R5 merchant test at unseen sites | this file, "Phase R5 (2026-11-07), PRE-REGISTERED before any R5 simulation" | 37f1aa2 (2026-11-07) | b48ffd1 (2026-11-07) |
| R6 oracle headroom, price-awareness | this file, "Phase R6 (2026-11-07), PRE-REGISTERED before any R6 run" | a0c0684 (2026-11-07) | 795d20a (2026-11-08); "Phase R6 results" in this file |
| R7 sensitivity (no decision rules) | this file, "Phase R7 (sensitivity, specified before the runs), 2026-11-08" | eb7f39d (2026-11-08); tools 426446e | 0d4038f (2026-11-08) |

Public releases: v1.1.0 (R4, 0c1f68e), v1.2.0 (R5, f47a2d8), v1.3.0 (R6, 962ef53), v1.4.0 (R7, f216484). The R3 code and results are in every release.
