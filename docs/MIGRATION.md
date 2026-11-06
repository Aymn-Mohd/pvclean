# Migration

The `legacy/` and `tests/legacy/` directories named here are not in this public release. They stay in the private development repository.

Where old code went. `legacy/` keeps the old module names as shims, so `import sim` still works with `legacy/` on the path. `tests/legacy/` runs the older tests that way. The old drivers are gone: use `python -m pvclean run <config>`.

## Modules

| old | new |
|---|---|
| `src/sim.py` CONFIG | `pvclean/defaults.yaml`, `pvclean/config.py` |
| `src/sim.py` plant and production | `pvclean/core/plant.py` |
| `src/sim.py` dust, exposure, rain forecast | `pvclean/core/soiling.py` |
| `src/sim.py` missions, access windows | `pvclean/core/robot.py` |
| `src/sim.py` simulate | `pvclean/core/simulator.py`, `pvclean/core/accounting.py`, `pvclean/policies/` |
| `src/sim.py` weather | `pvclean/weather/` |
| `src/sim.py` prices and values | `pvclean/markets/`, `pvclean/contracts/` |
| `src/sim.py` planner_inputs | `pvclean/core/inputs.py` |
| `src/forecasting.py`, `sim.fc_value` | `pvclean/forecasts/` |
| `src/evaluation.py`, `rx.ci95`, `rx.paired`, `cr.paired` | `pvclean/stats/intervals.py` |
| `rq1_decomp.decomp` | `pvclean/stats/decomposition.py` |
| `cr.verdict`, `rs.h_r2`, `robustness.robust` | `pvclean/stats/rules.py` |
| `src/exact.py` row_tables, schedule_value | `pvclean/exact/tables.py` |
| `src/exact.py` solve | `pvclean/exact/milp.py` |
| `src/exact.py` make_mpc, `src/optimisation.py` | `pvclean/exact/receding.py`, one version |
| `src/checks.py` | `pvclean/core/robot.py` |
| `experiments/belief_world.py` | `pvclean/exact/belief.py`, as a `World` |
| `rx.TRAIN`, `rx.TEST`, `rx.GRID` | `pvclean/protocol.yaml`, `Protocol`, `Runner` |
| `rx.tune`, `rx.evaluate`, `cr.tune`, `cr.evaluate` | `Runner.tune_params`, `Runner.evaluate_summary`, `Runner.tune`, `Runner.evaluate` |
| `src/real_prices_v2.py` | `pvclean/markets/build.py` |
| `src/build_new.py` sites, Dubai | `pvclean/weather/build.py` |
| `src/download_nasa_r3.py` | `pvclean/download.py`, without retries |

## Entry points

| old command | new command |
|---|---|
| `src/run_experiments.py` | `run configs/studies/generated.yaml` |
| `src/run_extra.py` | `run configs/studies/extra.yaml` |
| `src/run_new.py nrel`, `spain`, `wx` | `run configs/studies/nrel.yaml`, `spain.yaml`, `wx.yaml` |
| `src/run_real.py`, `run_roll.py`, `run_oracle.py`, `run_forecast.py` | `run configs/studies/real.yaml`, `roll.yaml`, `oracle.yaml`, `forecast.yaml` |
| `src/run_exact.py`, `run_exact_matched.py`, `run_mpc.py` | `run configs/studies/exact.yaml`, `exact_matched.yaml`, `mpc.yaml` |
| `experiments/price_aware_baseline.py` | `run configs/studies/ft_synthetic.yaml` |
| `experiments/real_market_replay.py` | `run configs/studies/replay.yaml` |
| `experiments/horizon_sensitivity.py` | `run configs/studies/horizon.yaml` |
| `experiments/matched_information.py` | `run configs/studies/belief_benchmark.yaml` |
| `experiments/forecast_audit.py` | `run configs/studies/forecast_audit.yaml` |
| `src/price_audit_r1.py` | `run configs/studies/price_audit.yaml` |
| `experiments/chrono_replay.py` | `run configs/studies/r1_chrono.yaml` |
| `experiments/rq1_decomp.py` | `run configs/studies/r1_decomp.yaml` |
| `experiments/sanity_tau.py` | `run configs/studies/r1_sanity_tau.yaml` |
| `experiments/robustness.py` | `run configs/studies/r1b_robust.yaml` |
| `experiments/claims_recheck.py` | `run configs/studies/r1b_claims.yaml` |
| `experiments/milp_gaps.py` | `run configs/studies/r1b_milp_gaps.yaml` |
| `experiments/failure_diag.py` | `run configs/studies/r1b_failure_diag.yaml` |
| `src/provenance_r1b.py` | `run configs/studies/r1b_audit_counts.yaml` |
| `experiments/robot_sweep.py` | `run configs/studies/r2_robot.yaml` |
| `experiments/mission_trace.py` | `run configs/studies/r2_trace.yaml` |
| `experiments/r2_checks.py` | `run configs/studies/r2_checks.yaml` |
| `experiments/matched_replay.py run`, `wx` | `run configs/studies/r3_matched.yaml`, `r3_site_weather.yaml` |
| `experiments/r3_checks.py` | `run configs/studies/r3_checks.yaml` |
| `experiments/posthoc_kappa.py` | `run configs/studies/r3_kappa.yaml` |
| `experiments/r3b_rain.py` | `run configs/studies/r3b_rain.yaml` |
| `src/make_outputs.py`, `_v10`, `_pes` | `report` |
| `src/make_r1_summary.py`, `_r2`, `_r3`, `src/claims_registry.py` | `report --summaries` |
| `src/make_r2_figures.py` | `report` |

The commands above start with `python -m pvclean`.

## Output files

- `r3_matched.yaml` writes `results_matched_r3.json` with keys `r3` and `r3_meta`. `belief_benchmark.yaml` writes `results_matched_belief.json` with `part_a` and `part_b`. The stored `results/results_matched.json` holds all four keys.
- `generated.yaml` leaves `ft` out of `rq1`, matching the stored `results.json`. The old script gained `ft` when it joined the grid.

## Moved unchanged, not maintained

`legacy/an_real.py`, `diag_real.py`, `real_prices.py`, `build_new.py`, `download_nasa_r3.py`, `reproduce_v9.py`, `runchain.sh`, `run_all.sh`. They use old paths. `run_all.sh` pushes to `main`: do not run it. `papers/e1_pes/build_main_v10.py` needs the absent `_v9paper` tree.

## Directories

`paper/` is now `papers/e1_pes/`. Files in `docs/` moved to `docs/records/` word for word, so paths inside those records still say `src/` and `docs/`.
