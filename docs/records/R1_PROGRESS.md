# R1b progress

- Stage 0: pulled, HEAD 2bef302 present, 33/33 tests pass.
- Stage 1: pre-registration addendum committed alone and pushed (4686bba).
- Stage 2: claim recheck (ANALYSIS) done: results/claims_recheck.json, R1_SUMMARY.md R1b.1-R1b.2; per-seed reruns reproduce stored means to 3.5e-12; 2 of 13 paper significance statements disagree (price merchant k3.0, NREL median merchant).
- Stage 3: robustness (a)-(d) run as pre-registered: results/results_robust.json, R1_SUMMARY.md R1b.3; planner-bestbase ROBUST 19/20, planner-FT ROBUST 14/20; Pool(3) == Pool(24) checked on 2 cells.
- Stage 4: docs/MILP_FORMULATION.md and docs/PLANNER_PSEUDOCODE.md written from the code; paired J*-J gaps, ratio-of-means vs mean-of-ratios and solver stats in results/milp_gaps.json (experiments/milp_gaps.py, stored results only). results_matched.json has no part_a (logged).
- Stage 5: failure diagnostics (DESCRIPTIVE): results/figures/r1b_diag_es_merchant_2024.pdf, r1b_diag_exact_merchant_c4.pdf, results/failure_diag.json, R1_SUMMARY.md R1b.4; sim.py gains an opt-in cfg diag log (decisions unchanged; rerun reproduces stored nets exactly).
- Stage 6: provenance: data/provenance/NLR.md, results/audit_counts.json (src/provenance_r1b.py); 146 sites, 0.10 and 0.30 %/day, 54 MAE pairs (rho -0.115, p 0.408) and 23,562 leakage checks all reproduce.
- Stage 7: R1_SUMMARY.md updated with all R1b results (labelled) and deviations 16-25; 37/37 tests pass.

# R2 progress

- R2 step 0: pulled, HEAD 9d57201, 37/37 tests pass.
- R2 step 1: sim.py gains battery_rows, availability (own stream, seed + 15485863) and the opt-in mission_log; night_min, service_min and speed_mps confirmed settable through the sweep job path; tests/test_r2.py added; defaults bit-identical to the stored R1 RQ1 rerun on every field of every seed (4 contracts, 8 arms, 50 seeds); 60/60 tests pass.
- R2 step 2: pre-registration committed alone and pushed (427dcfd), before any R2 run.
- R2 step 3: sweep run (11 distinct settings x 4 contracts, not 13: see R2 blockers); results/results_robot.json; default cells equal the R1 RQ1 rerun exactly; Pool(3) == Pool(24) on 2 cells; H-R2 per the rule: NOT SUPPORTED (9/12 means <= 0, 1 interval above 0, 5 below 0).
- R2 step 4: results/trace_merchant_default.json (seed 35, lower-middle of 50 by planner net; night before 2025-10-28, 13 rows; 36 missions logged), results/figures/fig_mission.pdf, fig_robot_sweep.pdf (vector, fonts embedded); experiments/r2_checks.py adds unregistered diagnostics in results/r2_checks.json.
- R2 step 5: docs/R2_SUMMARY.md (src/make_r2_summary.py) written; EXPERIMENT_LOG results added.

# R3 progress

- R3 step 0: pulled, HEAD 2db700f, 60/60 tests pass (project .venv).
- R3 step 1: pre-registration committed alone and pushed (ab9dfdb), before any download or R3 code.
- R3 step 2: 75 NASA POWER files (3 sites x 2001-2025) downloaded; URLs and sha256 in data/provenance/r3_nasa_power.json; no fill values or gaps; HR stamp checked as hour start; time-base, orientation and leakage tests pass (360 decision checks, 0 failures); yields and rain days in results/r3_site_weather.json.
- R3 step 3: sim.py gains opt-in site weather (wx_site, wx_site_years, clim_years, time_base, wx_npz, wx_wind); lat, lon, tilt, azimuth and soil_mean were already options. Defaults: 384 runs against the 2db700f sim.py equal on every field, stored R1 replay reproduced exactly; implementation notes committed before any R3 run.
- R3 step 4: replay finished (24 cases, 2288 s CPU, 2:29 wall, exit 0); results_matched.json keys r3, r3_meta added, part_b unchanged; two cases rerun at 5 workers identical to stored. H-R3 by the rule: NOT SUPPORTED (mean > 0 in 6 of 12).
- R3 step 5: docs/R3_SUMMARY.md (src/make_r3_summary.py) written; unregistered checks in experiments/r3_checks.py, results/r3_checks.json; EXPERIMENT_LOG results added; provenance note corrected to name build_new.py sites.
