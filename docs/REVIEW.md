# E1 code review

Review of the E1 repository before the `pvclean` restructure. Written 2026-11-05 from `archive/e1-pes-r1-20261105` (7008040). Sections 1 to 4 describe the code as found. Section 5 is the plan. Section 6 records what happened.

## 1. Branches

`main` is an ancestor of every other branch. `restructure` starts at `main` and fast-forwards to `e1-pes-r1`, because `main` lacks all work after 12 October, including every study the restructure must preserve.

| branch | last commit | date | commits ahead of main | files changed vs main (`git diff --stat main...branch`) | merged into main | in e1-pes-r1 | what main lacks |
|---|---|---|---|---|---|---|---|
| main | 94c699b | 2026-10-12 | 0 | 0 | yes | yes | base |
| e1-v10 | fd55d5e | 2026-10-16 | 1 | 63 files changed, 56273 insertions(+), 596 deletions(-) | no | yes | v10 code, tests, docs and paper sources |
| e1-pes | 87d448a | 2026-10-25 | 2 | 68 files changed, 56657 insertions(+), 596 deletions(-) | no | yes | v10 plus the PES energy metrics and 5-page paper |
| e1-pes-r1 | 7008040 | 2026-11-05 | 30 | 153 files changed, 716728 insertions(+), 623 deletions(-) | no | yes | everything in e1-pes plus R1, R1b, R2, R3, POST HOC kappa and R3b |
| e1-overlap-cleanup | be1206e | 2026-10-16 | 2 | 2 files changed, 5 insertions(+), 78 deletions(-) | no | no | removes the value-of-information outputs from make_outputs.py; adds an EXP-08 scope note to the log |
| GPU_HOST-runs | 1bcba4f | 2026-10-16 | 2 | 4 files changed, 584 insertions(+) | no | no | CLAUDE.md, one log line, docs/HORIZON_FILE_CHECK.md |

Local branches `e1-pes-r1`, `main` and `GPU_HOST-runs` match their remotes. `e1-v10`, `e1-pes` and `e1-overlap-cleanup` exist only on origin. All six heads are tagged `archive/<branch>-20261105` and pushed.

## 2. Code map

| file | lines | what it does | imported by | tests | writes |
|---|---|---|---|---|---|
| `experiments/belief_world.py` | 22 | Shared helper: deterministic 'belief world' in which the truth equals the information-matched planner's model: | matched_information | test_v10 | none |
| `experiments/chrono_replay.py` | 155 | Phase R1 (pre-registered in docs/EXPERIMENT_LOG.md): chronological real-market replay with interval-level valu | 8 scripts | test_posthoc_kappa, test_r2, test_r3 | results_chrono.json |
| `experiments/claims_recheck.py` | 99 | Phase R1b stage 2 (ANALYSIS): recheck of every sensitivity result the paper cites, from per-seed results. | entry point | none | claims_recheck.json |
| `experiments/failure_diag.py` | 191 | Phase R1b stage 5 (DESCRIPTIVE): failure diagnostics for one median-difference seed. | entry point | none | failure_diag.json, 2 figures |
| `experiments/forecast_audit.py` | 65 | EXP-07: forecast scenarios F0-F4 on real price years: error metrics and an automated no-lookahead (poison) aud | entry point | none | results_forecast_audit.json |
| `experiments/horizon_sensitivity.py` | 75 | EXP-03/04/05: horizon sensitivity, terminal value and information ladder for the receding-horizon exact optimi | entry point | none | results_horizon.json |
| `experiments/matched_information.py` | 83 | EXP-05: optimisation quality with everything but the decision rule held fixed. | entry point | none | results_matched.json (part_a, part_b) |
| `experiments/matched_replay.py` | 111 | Phase R3 (pre-registered in docs/EXPERIMENT_LOG.md): the R1 replay with the plant placed in each price market, | posthoc_kappa, r3_checks, r3b_rain | test_posthoc_kappa, test_r3, test_r3b | results_matched.json (r3), r3_site_weather.json |
| `experiments/milp_gaps.py` | 56 | Phase R1b stage 4 (ANALYSIS, from existing results only): paired absolute gaps J* - J of the exact benchmark. | entry point | none | milp_gaps.json |
| `experiments/mission_trace.py` | 73 | Phase R2 step 4: one-year mission trace for the figure (EXTENSION / DESCRIPTIVE). Merchant contract, default r | entry point | none | trace_merchant_default.json |
| `experiments/posthoc_kappa.py` | 96 | POST HOC after R3 (not pre-registered; note committed before the run in docs/EXPERIMENT_LOG.md, "POST HOC afte | entry point | test_posthoc_kappa | results_matched_posthoc_kappa.json |
| `experiments/price_aware_baseline.py` | 32 | EXP-06a: forecast-matched price-aware economic threshold ('ft') in the generated-market study (4 contracts, 50 | entry point | none | results_ft_synthetic.json |
| `experiments/r2_checks.py` | 95 | Phase R2 UNREGISTERED DIAGNOSTICS, run after the pre-registered sweep to check its surprises. Nothing here ent | entry point | none | r2_checks.json |
| `experiments/r3_checks.py` | 110 | Phase R3 UNREGISTERED DIAGNOSTICS, run after the pre-registered replay to check its surprises. Nothing here en | entry point | none | r3_checks.json |
| `experiments/r3b_rain.py` | 51 | Phase R3b (pre-registered in docs/EXPERIMENT_LOG.md): NASA POWER daily rain against gauge rain at the three R3 | entry point | test_r3b | results_r3b_rain.json |
| `experiments/real_market_replay.py` | 43 | EXP-06b/EXP-08: real-market replay (SA1, QLD1, OMIE ES 2023-2025; merchant and PPA) with forecast scenarios F0 | entry point | none | results_replay.json |
| `experiments/reproduce_v9.py` | 45 | EXP-01 / EXP-09: compare a fresh re-run of the v9 chain with the shipped v9 results, value by value, and regen | entry point | none | exp01_reproduce_v9.json (compares two trees) |
| `experiments/robot_sweep.py` | 133 | Phase R2 (EXTENSION, pre-registered in docs/EXPERIMENT_LOG.md "Phase R2"): robot-capability sweep on the gener | mission_trace, r2_checks | none | results_robot.json |
| `experiments/robustness.py` | 125 | Phase R1b stage 3 (SENSITIVITY, pre-registered in docs/EXPERIMENT_LOG.md "Phase R1b"): robustness of the gener | entry point | none | results_robust.json |
| `experiments/rq1_decomp.py` | 95 | Phase R1 ANALYSIS: revenue / energy / cost decomposition of planner-vs-FT and planner-vs-best-baseline differe | matched_replay | none | results_rq1_decomp.json |
| `experiments/sanity_tau.py` | 60 | Phase R1 ANALYSIS: single-row sanity check of the planner against the square-root cleaning interval. | entry point | test_sanity_tau | results_sanity_tau.json |
| `paper/build_main_v10.py` | 163 | Rebuilds main.tex v10 from the absent _v9paper tree. Guarded by --force. | entry point | none | none |
| `src/an_real.py` | 15 | Prints a summary of results_real.json. One-off. | entry point | none | none |
| `src/build_new.py` | 78 | Build hourly Spain prices (OMIE) and local-time Dubai weather years (NASA POWER). Run from src/. | entry point | none | data/real_prices.npz (ES), data/dubai_wx.npz, data/site_wx.npz |
| `src/checks.py` | 18 | Schedule validators and consistency checks used by experiments and tests. | horizon_sensitivity, matched_information | test_v10, test_r2 | none |
| `src/claims_registry.py` | 14 | EXP-09: list every number macro used in paper/main.tex with its value and defining file. | entry point | none | docs/CLAIMS_REGISTRY.md |
| `src/diag_real.py` | 21 | Prints a fold diagnostic. One-off. | entry point | none | none |
| `src/download_nasa_r3.py` | 51 | Phase R3: download NASA POWER hourly point data (UTC) for the three matched sites, 2001-2025, one request per  | entry point | none | data/raw/nasa_power, provenance |
| `src/evaluation.py` | 43 | Statistics at the right level of replication (v10). | price_aware_baseline, make_outputs_v10 | test_v10 | none |
| `src/exact.py` | 201 | EXP-01: exact (clairvoyant) benchmark on small instances. | 7 scripts | test_v10, test_invariants | none |
| `src/forecasting.py` | 61 | Causal forecast providers with explicit information timestamps (v10). | 5 scripts | test_v10, test_r1 | none |
| `src/make_outputs.py` | 516 | Generate figures, LaTeX tables and numbers.tex macros from results/results.json. | entry point | none | paper/numbers.tex, table_rq1, table_real, 5 figures (table_fore and table_exact are overwritten by v10) |
| `src/make_outputs_pes.py` | 88 | PES GM 2027 energy metrics (ANALYSIS, post-processing of existing results; no new runs). | entry point | none | paper/numbers_pes.tex, table_rq1_pes, macros_pes.json |
| `src/make_outputs_v10.py` | 159 | v10 tables and number macros. Reads results/*.json (v9 results that were re-run bit-identically in EXP-01, plu | entry point | none | paper/numbers_v10.tex, table_fore, table_exact, macros_v10.json |
| `src/make_r1_summary.py` | 253 | Write the generated tables of docs/R1_SUMMARY.md from results/results_chrono.json, results_rq1_decomp.json, pr | entry point | none | docs/R1_SUMMARY.md |
| `src/make_r2_figures.py` | 110 | Phase R2 figures from results/trace_merchant_default.json and results/results_robot.json: results/figures/fig_ | entry point | none | 2 figures |
| `src/make_r2_summary.py` | 113 | Writes docs/R2_SUMMARY.md from results/results_robot.json, results/r2_checks.json and results/trace_merchant_d | entry point | none | docs/R2_SUMMARY.md |
| `src/make_r3_summary.py` | 220 | Writes docs/R3_SUMMARY.md from results/results_matched.json, results/r3_site_weather.json, results/r3_checks.j | entry point | none | docs/R3_SUMMARY.md |
| `src/optimisation.py` | 112 | Receding-horizon exact (MILP) cleaning optimiser with configurable information, horizon and terminal value (v1 | horizon_sensitivity, matched_information | test_v10 | none |
| `src/price_audit_r1.py` | 56 | Phase R1 price audit: hourly-mean (v9/v10) versus interval-level valuation on the same contiguous R1 years. Ru | entry point | none | price_audit.json |
| `src/provenance_r1b.py` | 111 | Phase R1b stage 6 (provenance). Run from src/. | entry point | none | audit_counts.json, data/provenance/NLR.md |
| `src/real_prices.py` | 32 | Build hourly real price arrays [USD/kWh] for SA1 and QLD1, 2023-2025, from AEMO 5-min RRP. | entry point | none | data/real_prices.npz |
| `src/real_prices_v2.py` | 133 | Phase R1: hourly real-price arrays with interval-level contract valuation and no wrap-around. Run from src/. | price_audit_r1 | test_r1 | data/real_prices_v2.npz |
| `src/run_exact.py` | 38 | EXP-01 driver: exact clairvoyant optimum vs tuned heuristics on 6-row, 60-day instances. | entry point | none | results_exact.json |
| `src/run_exact_matched.py` | 33 | Information-matched exact benchmark. For each instance the optimiser plans open-loop on the planner's own beli | entry point | none | results_exact_matched.json |
| `src/run_experiments.py` | 220 | Tune every policy on training seeds, evaluate on held-out test seeds, write results JSON. | 22 scripts | test_posthoc_kappa, test_r2, test_r1, test_r3 | results.json |
| `src/run_extra.py` | 33 | Extra robustness: rain-day scale and manual-scale cleaning cost. Writes results/results_extra.json. | entry point | none | results_extra.json |
| `src/run_forecast.py` | 40 | EXP-02: forecast-information hierarchy on real prices (leave-one-price-year-out). | entry point | none | results_forecast.json |
| `src/run_mpc.py` | 27 | Information-matched benchmark: receding-horizon exact optimiser (14-day MILP, re-solved daily) with the statio | entry point | none | results_mpc.json |
| `src/run_new.py` | 83 | New-data experiments: (1) NREL-calibrated soiling sweep, (2) OMIE Spain replay, (3) real Dubai weather. | entry point | none | results_nrel.json, results_spain.json, results_wx.json |
| `src/run_oracle.py` | 16 | Same tuned parameters as the leave-one-year-out replay, but planner inputs built from the test price year. | entry point | none | results_oracle.json |
| `src/run_real.py` | 33 | Replay real AEMO prices (SA1, QLD1, 2023-2025) with leave-one-price-year-out tuning. | entry point | none | results_real.json |
| `src/run_roll.py` | 28 | Rolling-origin replay: tune and build planner inputs on the previous price year only, test on the next. | entry point | none | results_roll.json |
| `src/sim.py` | 700 | E1 simulation: contract-aware, row-level soiling maintenance for an agrisolar plant. | 26 scripts | test_r1b, test_v10, test_r2, test_r1, test_r3, test_invariants | none |

Other entry points: `runchain.sh` (paths under `HOME_DIR`, dead) and `results/run_all.sh` (resumable driver for six v10 stages; it commits and pushes to `main` after each stage).

### Flags

**Duplicates.** `_v9code`, `_v9paper`, `_v9repro` and `experiments/r3` are not in the tree (the first three are only `.gitignore` lines), and there is one copy of `sim.py`. Duplicated logic inside the tree: `exact.make_mpc` and `optimisation.make_mpc`; `ci95` in `run_experiments.py`, `make_outputs.py` and `an_real.py`; `paired` in `run_experiments.py` and `chrono_replay.py`; `tune` and `evaluate` in `run_experiments.py`, `chrono_replay.py` and `robustness.py`; the POA chain three times in `sim.py`; the gain calculation twice in `simulate`; `AUD_USD` and `EUR_USD` in two files each; `real_prices.py` and `real_prices_v2.py` as two price pipelines.

**Dead code.** `src/an_real.py`, `src/diag_real.py`, `runchain.sh`. Inside live files: the `if False` set expression and unused `rows_A` in `exact.solve`, `cfg["c_row"] * 0`, `k = n // 4 if ...` in `build_new.py`, `if y == 2024: pass` in `real_prices.py`, `if sh == "raw" and c == "ppa": pass` in `run_real.py`, `if sc == "F4" and pol == "ft": pass` in `make_outputs_v10.py`, unused `itertools`, `copy`, `sys` imports in `run_experiments.py`.

**Hard-coded paths.** 16 scripts use `../results`, `../data` or `../paper` and only work from one directory. `runchain.sh` uses `HOME_DIR`. `Pool(2)` remains in 15 files, although `docs/REPRODUCIBILITY.md` says it was replaced.

**Magic numbers outside config.** Weather generator (clear-sky index 0.97, sd 0.015, haze range, gamma shape and scale, temperature model, month rain and haze tables); albedo 0.25; wind 3 m/s; price model coefficients; seed offsets 7919, 104729, 31337, 15485863, 99991, site seed 7; row noise 0.15; storm season 0.8 and day 60, dust season day 75; mobile learning weights 0.6 and 0.4 and clip bounds; planner look-ahead 7 days; `rec >= 0.9`; roll window 28; training and test seed lists; planner-input seeds 2000 to 2009; parameter grids; exchange rates 0.65 and 1.08; MILP gaps and time limits.

**Missing tests.** No test covers a study driver end to end, the output generators, the price and weather builders, or `exact.make_mpc` beyond one check. No regression files, no smoke test, no continuous integration.

## 3. Provenance of results/

Commit = first commit that added the file, then last commit that changed it. Stored files carry no commit or config stamp, so the script and config columns come from reading the code. Seeds: TRAIN = 1000 to 1004, TEST = 0 to 49, INP = planner inputs 2000 to 2009. The last column is filled from the rerun in section 6.

| file | script | config | seeds | commit (added, last) | rerun |
|---|---|---|---|---|---|
| `audit_counts.json` | src/provenance_r1b.py | stored results | none | 8398564, 8398564 | 0 |
| `check_L7_vs_clairvoyant.json` | no script in tree | unknown | unknown | 290d5be, 290d5be | not rerun: no script or hand-made |
| `claims_recheck.json` | experiments/claims_recheck.py | stored and rerun cells | TRAIN, TEST | a897745, a897745 | 0 |
| `exp01_reproduce_v9.json` | experiments/reproduce_v9.py | needs the absent v9 tree | none | fd55d5e, fd55d5e | not rerun: no script or hand-made |
| `failure_diag.json` | experiments/failure_diag.py | one median seed, 2 cases | stored | 5daa129, 5daa129 | 0 |
| `horizon_summary_transcribed.json` | hand transcription | fallback input of make_outputs_v10.py; unused while results_horizon.json has 680 records | none | fd55d5e, fd55d5e | not rerun: no script or hand-made |
| `macros_pes.json` | src/make_outputs_pes.py | results.json | none | 87d448a, 87d448a | byte-identical |
| `macros_v10.json` | src/make_outputs_v10.py | stored results | none | fd55d5e, fd55d5e | byte-identical |
| `manifest.json` | no script in tree | hash list written during v10 | none | fd55d5e, fd55d5e | not rerun: no script or hand-made |
| `milp_gaps.json` | experiments/milp_gaps.py | stored results only | stored | 4136656, 4136656 | 0 |
| `price_audit.json` | src/price_audit_r1.py | 5 markets | TEST | 2bef302, 2bef302 | 0 |
| `r2_checks.json` | experiments/r2_checks.py | frozen, use, low, retune | TRAIN, TEST | eca5daf, eca5daf | 0 |
| `r3_checks.json` | experiments/r3_checks.py | shift 182 days; retune seeds 1005-1019 | TRAIN, TEST | a0ec103, a0ec103 | 0 |
| `r3_site_weather.json` | experiments/matched_replay.py wx | SITES | none | dbeeef6, dbeeef6 | 0 |
| `results.json` | src/run_experiments.py | CONFIG; RQ1, RQ3, sensitivity, price sweep | TRAIN, TEST, INP | fd55d5e, fd55d5e | 5.8e-11 (2590 of 6947) |
| `results_chrono.json` | experiments/chrono_replay.py | R1 folds, MODES F2, CLIM, F3, F4 | TRAIN, TEST | 2bef302, 2bef302 | 0 |
| `results_exact.json` | src/run_exact.py | 6 rows, days 120-180, night 100 min, c_row 4, 12 | seeds 0-19 | fd55d5e, fd55d5e | 9.1e-13 (217 of 1144) |
| `results_exact_matched.json` | src/run_exact_matched.py | as results_exact | seeds 0-19 | fd55d5e, fd55d5e | 9.1e-13 (18 of 240) |
| `results_extra.json` | src/run_extra.py | rain_scale 1, 2, 3; c_row 24, 48 | TRAIN, TEST, INP | fd55d5e, fd55d5e | 7.3e-12 (62 of 116) |
| `results_extra_20yr.json` | no script in tree (v9 era) | unknown | unknown | fd55d5e, fd55d5e | not rerun: no script or hand-made |
| `results_forecast.json` | src/run_forecast.py | fc_mode clim, roll, dayahead, perfect | TRAIN, TEST | fd55d5e, fd55d5e | 8.2e-12 (124 of 204) |
| `results_forecast_audit.json` | experiments/forecast_audit.py | 7-day horizon, 3 markets | INP | 3d4e18c, fd55d5e | 5.6e-16 (33 of 1011) |
| `results_ft_synthetic.json` | experiments/price_aware_baseline.py | CONFIG, 5 policies | TRAIN, TEST | bfd86bc, fd55d5e | 4.4e-11 (503 of 1244) |
| `results_horizon.json` | experiments/horizon_sensitivity.py | 680 runs, MILP gap 1e-3, 60 s limit | seeds 0-19 | 3d4e18c, 7076564 | 9.1e-13 (69 of 10880) |
| `results_matched.json` | experiments/matched_information.py (part_a, part_b); experiments/matched_replay.py (r3, r3_meta) | R3: SITES, soil 0.30 and 0.11 %/day | TRAIN, TEST | 1f25e6d, d69f238 | 0 (r3) |
| `results_matched_posthoc_kappa.json` | experiments/posthoc_kappa.py | kappa grid to 32, F2, 0.30 %/day | TRAIN, TEST | ab4c5ac, ab4c5ac | 0 |
| `results_mpc.json` | src/run_mpc.py | as results_exact, 14-day MILP | seeds 0-19 | fd55d5e, fd55d5e | 4.5e-13 (10 of 240) |
| `results_nrel.json` | src/run_new.py nrel | soil_mean 0.0011, 0.0019, 0.0030 at season_amp 0.16 | TRAIN, TEST, INP | fd55d5e, fd55d5e | 4.4e-11 (747 of 1656) |
| `results_oracle.json` | src/run_oracle.py | parameters from results_real.json | TEST | fd55d5e, fd55d5e | 2.9e-11 (1832 of 4044) |
| `results_r3b_rain.json` | experiments/r3b_rain.py | NASA side only, no gauge data | none | 51464a0, 51464a0 | 0 |
| `results_real.json` | src/run_real.py | real_market SA1, QLD1; aligned, raw; vexp_q None, 0.99, 0.95 | TRAIN, TEST | fd55d5e, fd55d5e | 3.6e-11 (10803 of 24264) |
| `results_replay.json` | experiments/real_market_replay.py | F0-F4, roll_min_hist 1 | TRAIN, TEST | 290d5be, fd55d5e | 5.8e-11 (5499 of 12420) |
| `results_robot.json` | experiments/robot_sweep.py | 11 settings x 4 contracts | TRAIN, TEST | 43e1b11, 43e1b11 | 0 |
| `results_robust.json` | experiments/robustness.py | 5 variants, chains +0, +10000, +20000 | TRAIN, TEST | 237198b, 237198b | 0 |
| `results_roll.json` | src/run_roll.py | previous-year folds | TRAIN, TEST | fd55d5e, fd55d5e | 2.9e-11 (1172 of 2696) |
| `results_rq1_decomp.json` | experiments/rq1_decomp.py | 7 policies, 4 contracts | TRAIN, TEST | 2bef302, 2bef302 | 0 |
| `results_sanity_tau.json` | experiments/sanity_tau.py | one row, tau 7.3, 15.7, 41.2 | none | 2bef302, 2bef302 | 0 |
| `results_spain.json` | src/run_new.py spain | real_market ES_raw, LOYO and rolling folds | TRAIN, TEST | fd55d5e, fd55d5e | 8.2e-12 (43 of 194) |
| `results_v1_old_exposure.json` | no script in tree (v9 era) | old exposure model | unknown | fd55d5e, fd55d5e | not rerun: no script or hand-made |
| `results_v2_20yr.json` | no script in tree (v9 era) | unknown | unknown | fd55d5e, fd55d5e | not rerun: no script or hand-made |
| `results_wx.json` | src/run_new.py wx | wx_years 2002-2009 train, 2010-2025 test | TRAIN, seeds 0-47 | fd55d5e, fd55d5e | 2.2e+01 (585 of 1584) |
| `trace_merchant_default.json` | experiments/mission_trace.py | merchant, default robot | median test seed | eca5daf, eca5daf | 0 |

Logs and timing files (`log_*.txt`, `time_*.txt`) belong to the script of the same name. Files added in fd55d5e came in one v10 import, so that commit is an upper bound on when they were produced, not the run itself.

## 4. Issues, ranked

| # | severity | issue | action |
|---|---|---|---|
| 1 | high | `main` is 30 commits behind `e1-pes-r1`. A branch from `main` alone would hold none of the studies to preserve. | Fast-forward `restructure` to `e1-pes-r1`. |
| 2 | high | Downloaded and derived market and weather data are tracked in git (`data/*.npz`, `data/new/*`, 29 MB). This conflicts with the no-data rule and with "nothing redistributed". The repository is private. | Remove from the tip; serve from a cache outside git. History keeps them: see the report. |
| 3 | high | `data/real_prices.npz` cannot be rebuilt: `src/real_prices.py` reads `data/aemo_merged/`, which does not exist. Six stored results and several paper macros depend on this file. | Keep the file in the cache with its hash on record; document it in DATA.md. |
| 4 | high | `belief_world.py` swaps functions inside the `sim` module, and scripts mutate `rx.TEST`, `rx.TRAIN`, `rx.GRID` and `cr.MODES`. Results depend on hidden global state. | Pass a `World` and explicit seeds and grids. |
| 5 | high | `simulate` is one 260-line function with every policy inline. A new policy or contract means editing core code. | Policy and contract interfaces with registries. |
| 6 | high | `src/make_outputs.py` needs data files, so paper macros cannot be regenerated without the data. | Store the few derived numbers in `results/macro_inputs.json`. |
| 7 | medium | `download_nasa_r3.py` retries 5 times with back-off. The rules forbid retries on blocked sources. | One attempt per URL in `pvclean download`. |
| 8 | medium | `if rec >= 0.9` in `simulate` is tied by a literal to the default `rain_full_recov`. Setting that below 0.9 silently stops the reset of `tau` and `A`. | Move to the config key `rain_reset_recov`, same value. |
| 9 | medium | Planner horizons run past `d1` but FT horizons stop at `d1`. In short-window instances the two see different horizons. | Behaviour kept. Documented. |
| 10 | medium | `exact.expected_increment` ignores `season_shift`, so a shifted run would give the MILP the wrong season. No stored result uses both. | Behaviour kept. Documented. |
| 11 | medium | Results carry no commit or config stamp. Five files have no producing script. | New runs record config and commit. Old files listed in section 3. |
| 12 | medium | `results/run_all.sh` commits and pushes to `main` by itself. | Moved to `legacy/`, not run. |
| 13 | medium | No `pyproject.toml`, no pinned versions; 15 files keep `Pool(2)` against `docs/REPRODUCIBILITY.md`. | `pyproject.toml` with pins; worker count from config. |
| 14 | medium | No regression tests and nothing tests the output generators. | Phase 2 golden tests. |
| 15 | low | Duplicates and dead code listed in section 2. | Merged or moved to `legacy/`. |
| 16 | low | `clear_sky` cache key omits `alt`, and `_SITE` holds both raw tables and site years. | Kept for `clear_sky` results; cache split. |
| 17 | low | `paper/table_real.tex` is generated but was never tracked, and the paper does not input it. | Still generated. Left untracked. |
| 18 | low | Tables in `docs/R3_SUMMARY.md` section 7 have more cells than headers, because `lab()` contains pipes. | Records stay word for word. Noted only. |
| 19 | low | `paper/build_main_v10.py` needs the absent `_v9paper` tree and a `--force` flag. | Moved with the paper, not run. |
| 20 | low | `checks.schedule_violations` raises IndexError on an out-of-range row, although it is meant to count it as a violation. | Behaviour kept. Documented. |

## 5. Plan

The target layout in the brief stands, with these changes.

1. `pvclean/exact/` is added for the MILP code. It is neither a study runner nor a policy: `policies/mpc.py` and `studies/` both call it.
2. `pvclean/config.py` and `pvclean/defaults.yaml` are added: one flat parameter set with the current values, which every study overrides.
3. `pvclean/data.py` and `pvclean/download.py` are added for the cache and provenance. The brief asks for both but names no module.
4. `pvclean/core/world.py` is added. It carries the weather, dust, exposure and value functions, which replaces the swapping of `sim` functions in `belief_world.py`.
5. Tests from before the restructure move to `tests/legacy/` and run against shims in `legacy/`, as a second check of behaviour.
6. `e1-overlap-cleanup` is not merged: its code change deletes paper macros, which would break the byte-identity rule. Its log note goes in `docs/records/decisions.md`.
7. From `GPU_HOST-runs`, `CLAUDE.md` is taken. Its log line goes in `docs/records/decisions.md`, so that `EXPERIMENT_LOG.md` stays word for word.

Order: golden tests on the unchanged code, then moves in small commits with tests after each, then verification, README, finish.

## 6. Outcome

Closed 2026-11-06. Code finished 2026-11-05. The rerun column of section 3 gives the largest difference between the `pvclean` rerun and the stored file. `docs/REPRODUCE.md` has the full table and the reasons.

**Issues.**

| # | outcome |
|---|---|
| 1 | Fixed: `restructure` holds all of `e1-pes-r1`. |
| 2 | Fixed at the tip. History and the archive tags still hold the files. |
| 3 | Not fixable: the input is gone. Recorded in `docs/DATA.md`. |
| 4, 5, 6 | Fixed: `World`, `Runner`, `Protocol`, `Policy`, registries, `results/macro_inputs.json`. |
| 7 | Fixed: `pvclean/download.py`. The old script is in `legacy/`, unmaintained. |
| 8 | Fixed: `rain_reset_recov`. |
| 9, 10, 20 | Kept as they are, because behaviour must not change. |
| 11 | Partly fixed: studies now have configs, but outputs carry no commit stamp, because that would change stored file shapes. |
| 12 | Fixed: moved to `legacy/`. |
| 13 | Fixed: `pyproject.toml`; workers come from the protocol. |
| 14 | Fixed: `tests/regression/`. There is still no continuous integration. |
| 15 | Fixed, except dead lines in the reporting code, which stay so that output cannot move. |
| 16 | Kept: `_SITE` holds both tables and years, because the older tests read it. |
| 17 | Kept: `table_real.tex` is still generated and untracked. |
| 18 | Kept: records stay word for word. |
| 19 | Kept: moved with the paper, not run. |

**Reason for each layout change.** See section 5. Added after that plan: `pvclean/model.py` (one place for public calls) and `pvclean/studies/runner.py` and `study.py`. Audit and diagnostic runners sit beside the five named runner types, one module each, because they are one-off studies with their own logic.

**Where branch content went.** `e1-v10`, `e1-pes`, `e1-pes-r1`: all of it, by fast-forward. `GPU_HOST-runs`: `CLAUDE.md`, and its log line in `docs/records/decisions.md`. `e1-overlap-cleanup`: its log note in `docs/records/decisions.md`; its code change is not taken.
