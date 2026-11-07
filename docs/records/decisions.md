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
