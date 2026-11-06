# Reproduce

Every stored result, the study that reruns it, and how close the rerun came. Reruns used `pvclean` on the GPU_HOST on 2026-11-05, 24 workers, nice 10, Python 3.13.16, with the pinned versions in `pyproject.toml`.

## Paper outputs

One command builds every table, macro file and figure from `results/`. It takes about 3 s and needs no data downloads. There is no switch for a single file.

```bash
python -m pvclean report
```

To rebuild an output from scratch, rerun the studies in the last column, compare `runs/<study>/` with `results/`, and then run the report. Reruns never write to `results/`, and the report reads only `results/`. Run times are in the Studies table.

| output | rebuild | stored inputs | studies behind the inputs |
|---|---|---|---|
| `papers/e1_pes/numbers.tex` | `python -m pvclean report` | `results.json`, `results_extra.json`, `results_nrel.json`, `results_wx.json`, `results_real.json`, `results_oracle.json`, `results_roll.json`, `results_spain.json`, `results_forecast.json`, `results_exact.json`, `results_mpc.json`, `macro_inputs.json` | generated, extra, nrel, wx, real, oracle, roll, spain, forecast, exact, mpc |
| `papers/e1_pes/numbers_v10.tex`, `results/macros_v10.json` | `python -m pvclean report` | `results_replay.json`, `results_ft_synthetic.json`, `results_exact.json`, `results_matched.json`, `results_horizon.json`, `results_forecast_audit.json` | replay, ft_synthetic, exact, r3_matched, belief_benchmark, horizon, forecast_audit |
| `papers/e1_pes/numbers_pes.tex`, `results/macros_pes.json` | `python -m pvclean report` | `results.json` | generated |
| `papers/e1_pes/table_rq1.tex` | `python -m pvclean report` | `results.json` | generated |
| `papers/e1_pes/table_rq1_pes.tex` | `python -m pvclean report` | `results.json`, through `table_rq1.tex` | generated |
| `papers/e1_pes/table_fore.tex` | `python -m pvclean report` | `results_replay.json` | replay |
| `papers/e1_pes/table_exact.tex` | `python -m pvclean report` | `results_exact.json`, `results_matched.json`, `results_horizon.json` | exact, belief_benchmark, horizon |
| `papers/e1_pes/table_real.tex` (untracked, not used by the paper) | `python -m pvclean report` | `results_real.json`, `results_oracle.json`, `results_roll.json` | real, oracle, roll |
| `papers/e1_pes/fig_price.pdf`, `fig_voi.pdf`, `fig_cv.pdf`, `fig_sens.pdf`, `fig_example.pdf` | `python -m pvclean report` | `results.json` | generated |
| `results/figures/fig_mission.pdf` | `python -m pvclean report` | `trace_merchant_default.json` | r2_trace |
| `results/figures/fig_robot_sweep.pdf` | `python -m pvclean report` | `results_robot.json` | r2_robot |
| `results/figures/r1b_diag_es_merchant_2024.pdf`, `r1b_diag_exact_merchant_c4.pdf` | `python -m pvclean run configs/studies/r1b_failure_diag.yaml` | none | r1b_failure_diag |
| `docs/records/R1_SUMMARY.md`, `R2_SUMMARY.md`, `R3_SUMMARY.md`, `CLAIMS_REGISTRY.md` | `python -m pvclean report --summaries` | stored results | as above |
| `results/macro_inputs.json` | `python -m pvclean report --refresh-inputs` | `results.json`; cache `real_prices.npz`, `dubai_wx.npz` | none |

The 7 tracked `.tex` files and 2 macro JSON files are byte-identical to the stored copies, and `tests/regression/test_paper_outputs.py` checks this. The summaries and `CLAIMS_REGISTRY.md` also came out byte-identical. No script here builds the LaTeX into a PDF.

## Studies

This release stores only the results that the paper macros and summary tests read. The table also lists other stored files from the development repository, for reference.

```bash
python -m pvclean run configs/studies/<study>.yaml
```

The difference column is the largest absolute difference between the rerun and the stored file, with the count of values that differ. Run-time and worker fields are left out. Run times are wall-clock seconds on 24 workers at nice 10. forecast_audit, r1_sanity_tau, r1b_milp_gaps, r1b_audit_counts, r3_site_weather and r3b_rain were timed on 2026-11-06, the rest on 2026-11-05. Times on other machines will differ.

| stored file | study | values | difference from stored | run time (s) | cache files |
|---|---|---|---|---|---|
| `results.json` | generated | 6947 | 5.8e-11 (2590 of 6947) | 177 | none |
| `results_ft_synthetic.json` | ft_synthetic | 1244 | 4.4e-11 (503 of 1244) | 21 | none |
| `results_extra.json` | extra | 116 | 7.3e-12 (62 of 116) | 26 | none |
| `results_nrel.json` | nrel | 1656 | 4.4e-11 (747 of 1656) | 17 | none |
| `results_wx.json` | wx | 1584 | 2.2e+01 (585 of 1584) | 23 | `dubai_wx.npz` |
| `results_spain.json` | spain | 194 | 8.2e-12 (43 of 194) | 48 | `real_prices.npz` |
| `results_real.json` | real | 24264 | 3.6e-11 (10803 of 24264) | 274 | `real_prices.npz` |
| `results_roll.json` | roll | 2696 | 2.9e-11 (1172 of 2696) | 31 | `real_prices.npz` |
| `results_oracle.json` | oracle | 4044 | 2.9e-11 (1832 of 4044) | 22 | `real_prices.npz` |
| `results_forecast.json` | forecast | 204 | 8.2e-12 (124 of 204) | 197 | `real_prices.npz` |
| `results_replay.json` | replay | 12420 | 5.8e-11 (5499 of 12420) | 353 | `real_prices.npz` |
| `results_forecast_audit.json` | forecast_audit | 1011 | 5.6e-16 (33 of 1011) | 4 | `real_prices.npz` |
| `price_audit.json` | price_audit | 256 | 0 | 64 | `real_prices_v2.npz` |
| `results_chrono.json` | r1_chrono | 201302 | 0 | 223 | `real_prices_v2.npz` |
| `results_rq1_decomp.json` | r1_decomp | 18715 | 0 | 11 | none |
| `results_sanity_tau.json` | r1_sanity_tau | 107 | 0 | 1 | none |
| `results_robust.json` | r1b_robust | 53905 | 0 | 56 | none |
| `claims_recheck.json` | r1b_claims | 3783 | 0 | 19 | none |
| `milp_gaps.json` | r1b_milp_gaps | 641 | 0 | 1 | none |
| `failure_diag.json` | r1b_failure_diag | 702 | 0 | 44 | `real_prices_v2.npz` |
| `audit_counts.json` | r1b_audit_counts | 428 | 0 | 1 | `new/nlr_monthly.csv`, `new/nlr_sites.csv` |
| `results_robot.json` | r2_robot | 119545 | 0 | 90 | none |
| `trace_merchant_default.json` | r2_trace | 3128 | 0 | 1 | none |
| `r2_checks.json` | r2_checks | 3241 | 0 | 177 | none |
| `r3_site_weather.json` | r3_site_weather | 327 | 0 | 4 | `site_wx.npz` |
| `r3_checks.json` | r3_checks | 2616 | 0 | 361 | `site_wx.npz`, `real_prices_v2.npz` |
| `results_matched_posthoc_kappa.json` | r3_kappa | 35273 | 0 | 35 | `site_wx.npz`, `real_prices_v2.npz` |
| `results_r3b_rain.json` | r3b_rain | 72 | 0 | 1 | `site_wx.npz` |
| `results_exact.json` | exact | 1144 | 9.1e-13 (217 of 1144) | 43 | none |
| `results_exact_matched.json` | exact_matched | 240 | 9.1e-13 (18 of 240) | 32 | none |
| `results_mpc.json` | mpc | 240 | 4.5e-13 (10 of 240) | 35 | none |
| `results_matched.json r3, r3_meta` | r3_matched | 163837 | 0 | 149 | `site_wx.npz`, `real_prices_v2.npz` |
| `results_matched.json part_b` | belief_benchmark | 196 | 9.1e-13 (46 of 196) | 186 | none |
| `results_horizon.json` | horizon | 10880 | 9.1e-13 (69 of 10880) | 709 | none |

Every study above also matches the archived code rerun on this machine bit for bit, where both read the same stored inputs. The one exception is `generated`, which leaves out the `ft` entries described below. `tests/regression` covers the five study types in about a minute.

## Data each study needs

Studies with `none` in the table run on a fresh clone. The others read these files from the data cache (see `docs/DATA.md`). The cache files listed were found by running each study on an empty cache and adding each file it asked for, then stopping after 25 s, so a read later in a long run would not show.

| cache file | how to get it |
|---|---|
| `real_prices.npz` | Cannot be rebuilt or downloaded. Needs a kept copy; `docs/DATA.md` has the hash. |
| `real_prices_v2.npz` | `python -m pvclean download aemo`, `python -m pvclean download omie`, then `pvclean.markets.build.build()`. Also needs `new/omie.csv`, which no script fetches. |
| `site_wx.npz` | `python -m pvclean download nasa-power`, then `pvclean.weather.build.sites()`. |
| `dubai_wx.npz` | `pvclean.weather.build.dubai()`, from `new/nasa_dubai.csv.gz`, which no script fetches. |
| `new/nlr_monthly.csv`, `new/nlr_sites.csv` | No script fetches these. See `data/provenance/NLR.md`. |

## Why some files differ from stored

- **About 1e-11.** Files from before R1 differ from the archived code too, so the restructure did not cause this. The cause was not found. An older machine or library build would explain differences of this size, but that was not tested.
- **`results_wx.json`, one value of 21.6 USD.** PPA, planner, seed 39. All other values agree to 1e-10. A near-tie decision flipping on float noise would explain it, but that was not tested. The stored paired mean is 70.55 and the rerun gives 71.00. The macro `WxPpaGain` is built from the stored file and prints 71.
- **`results.json`.** The archived script now adds `ft` to `rq1`, because `ft` joined the grid after the file was stored. `generated.yaml` leaves it out, so the shape matches the stored file.

## Not reproducible from this repository

- `results_matched.json` `part_a` is not in the stored file: it was dropped in fd55d5e. It remains in commit 1f25e6d. `belief_benchmark.yaml` regenerates it, and the rerun matches the archived code.
- `results_extra_20yr.json`, `results_v1_old_exposure.json`, `results_v2_20yr.json`, `check_L7_vs_clairvoyant.json` and `manifest.json` have no producing script.
- `exp01_reproduce_v9.json` needs the absent v9 tree. `horizon_summary_transcribed.json` is a hand transcription and is not used while `results_horizon.json` is present.
