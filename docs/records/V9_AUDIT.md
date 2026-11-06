# V9 audit (written before any v10 manuscript change)

Auditor: the v10 release process (same author team's tooling; this is a self-audit, not an independent review).
Date of audit: 2026-10-10. Scope: `E1_overleaf_v9.zip` (SHA-256 `29879ae6…12b2`) and `E1_simulation_code_v9.zip` (SHA-256 `68e954aa…8b51`).
Status labels used below: **VERIFIED** (re-derived in v10 from code), **RECONSTRUCTED** (rebuilt, not the v9 run), **UNVERIFIED**, **DEFECT**, **RISK**.

## 1. What v9 actually shipped

| Artefact | Content | Executable? |
|---|---|---|
| Overleaf zip | `main.tex`, `numbers.tex` (462 macros, auto-generated), `table_rq1/fore/exact.tex`, `refs.bib`, `main.bbl`, `fig_price.pdf` | LaTeX only |
| Code zip | `src/sim.py` (simulator), `src/exact.py` (MILP benchmarks), `run_*.py` drivers, `make_outputs.py` (writes numbers/tables/figure), `tests/test_invariants.py` (10 tests), `data/` (processed arrays, NREL, OMIE, NASA POWER), `results/*.json`, `results/manifest.json` (SHA-256), `reproduce.sh` | yes |
| Not shipped | raw AEMO 5-min CSVs (`data/aemo_merged/`; only the hourly arrays in `data/real_prices.npz`), solver logs for the receding-horizon optimiser, hardware/solver-version record | – |

The code zip is byte-identical (`src/`) to the working tree that produced the v9 tables. Executable code therefore **did exist** for v9; the earlier reviewer comment that it was missing referred to the Overleaf zip only.

## 2. Model summary (as implemented, not as described)

* Plant: 40 rows × 25 kWp, DC/AC 1.25, hourly pvlib clear-sky (Ineichen–Perez) × generated clearness, Erbs decomposition, Faiman cell temperature, −0.35 %/K. Site: 25.2°N, 55.3°E.
* Soiling: site-level daily lognormal increment × seasonal factor `1+0.4 sin(2π(d−75)/365)` + storms (≈3/yr, +1–4 %) × row exposure (CV 0.215, fixed site seed 7) × row noise (CV 0.15). Floor 0.5. Rain recovery: ≥5 mm 90 %, 1–5 mm 20 % of the gap to 0.995. **Synthetic; not fitted to measured Dubai soiling.**
* Contracts: fixed 0.06 USD/kWh; merchant `max(spot,0)`; PPA 0.05 if spot ≥ 0 else 0; capped (75 % of AC rating).
* Costs (assumptions): 4 USD/row, 10 USD/mission, 0.25 USD/row inspection. Night budget 360 min, 25 min/row service, 0.5 m/s travel. Odd rows closed for three 5-day windows (days 60, 150, 300).
* Station information (`info="site"`): the planner's estimate decreases by the **realised** site-level increment each day (it sees realised site dust, not row exposure) and recovers on observed rain.
* Policies: fixed interval, loss threshold, constant-price economic (`econ`), proposed planner `Φ_i = g_i τ_i − A_i − c_row` with κ/β mission dispatch, blackout anticipation, 2-day imperfect rain gate (80 % hit, 5 % false alarm).
* Protocol: tune on seeds 1000–1004, test on seeds 0–49, planner climatology from seeds 2000–2009; real markets leave-one-price-year-out (LOYO).

## 3. Data provenance and unit/time handling

| Data | Source (as recorded in v9 README) | Handling | v10 concern |
|---|---|---|---|
| AEMO SA1/QLD1 RRP 2023–2025 | AEMO 5-min regional reference price | interval-end → start; hourly mean; Feb 29 dropped; × 0.65 USD/AUD /1000 → USD/kWh; array rolled by 182 days | NEM time (AEST, no DST) hour index is used as the Dubai plant clock hour index: **no solar-time alignment** (1–2 h offset to local solar noon in SA/QLD). Prices not clipped; spikes (market cap) stay in. Fixed exchange rate. |
| OMIE ES 2023–2025 | OMIE day-ahead, 15-min periods from Oct 2025 | 15-min → hourly mean; 23/25-h DST days linearly resampled to 24 h (**distorts the price shape on 2 days/yr**); × 1.08 /1000 | CET/CEST market hour index used as plant clock. |
| NASA POWER Dubai 2002–2025 | hourly all-sky/clear-sky GHI, T2M, PRECTOTCORR | UTC → local (+4 h), Feb 29 dropped | reanalysis rain (not gauge). |
| NREL soiling map (146 sites, monthly rates) | NREL/NLR site table | summary statistics only | US sites, not Gulf. |
| Soiling in all main results | **generated** | – | no measured Dubai soiling; sensitivity only. |

## 4. Numerical-claim register (v9 abstract and body)

Status for each row is re-derived in v10: see `docs/EXPERIMENT_LOG.md` (EXP-01 and EXP-09). The column "source" is the shipped result file.

| Claim (macro) | v9 value | Source |
|---|---|---|
| Gain over best baseline, fixed / merchant / PPA / capped (`GainBest*`) | 84±29 / 157±40 / 70±34 / 23±28 USD/yr | `results.json` |
| Share of robot value (`GainPct*`) | 0.3 % / 1.0 % | `results.json` |
| Climatology planner below best baseline (`ForeClimNeg/ForeN`) | 15 of 18 price-year tests | `results_forecast.json` |
| Rolling gain range, positive years (`ForeRoll*`) | +28 to +338 USD/yr; 15 of 18 | `results_forecast.json` |
| Day-ahead / perfect gain range (`ForeDay*`, `ForePerf*`) | +81…+502; +78…+595 | `results_forecast.json` |
| Exact benchmark: clairvoyant (USD/instance) | 154 / 87 / 65 / 22 | `results_exact.json` |
| Planner share of clairvoyant (`Ex*Prop`) | 91 / 78 / 64 / 21 % | `results_exact.json` |
| Matched optimiser share (`ExMpc*`) | 92 / 87 / 95 / **9** % | `results_mpc.json` |
| Real-weather replay gains (`Wx*Gain`) | fixed +35±45, merchant +158±36, PPA +71±33 | `results_wx.json` |
| NREL median-rate sweep (`NrelMed*`) | fixed −30±45, merchant +48±47 | `results_nrel.json` |

## 5. Findings

**A1 — DEFECT (terminology and logic). "Information regret / optimisation regret".** v9 defines information regret = clairvoyant − matched MPC and optimisation regret = matched MPC − planner, and states that the matched optimiser "attributes most of that regret to information". This requires the matched MPC to be an upper bound on every policy using the same information. It is not: its model ignores row exposure and rain, uses expected dust, a 14-day horizon and no terminal value, and v9 itself reports the tuned fixed interval beating it (fixed tariff, 4 USD/row) and a *negative* optimisation regret (−3 USD) in one setting. The decomposition is therefore not identified. v10 replaces it with: `J*_clairvoyant`, `J_MPC`, `J_heuristic`; "clairvoyant-reference gap" `J* − J_MPC`; "observed policy-performance difference" `J_MPC − J_heuristic`.

**A2 — DEFECT (unexplained result). Matched optimiser = 9 % in merchant, 12 USD/row.** Per-seed data (`results_mpc.json`): mean gain 1.97 USD, mean cleanings 0.3 per instance (it essentially never cleans), versus clairvoyant 21.6 USD (sd 12.4) and tuned heuristics 5–8 USD. v9 stored no solver status, MIP gap, dual bound or runtime for the 14-day MILPs (`results_mpc.json` holds only gain and cleaning count), so correctness of the solves could not be audited from the shipped files. MPC options were `time_limit=20 s`, `mip_rel_gap=1e-3`. The MPC was also **untuned** while heuristics were tuned on training seeds. v10 investigates with controlled experiments (EXP-02…05).

**A3 — DEFECT (labelling). "Day-ahead" for AEMO.** The `dayahead` arm gives the planner the realised prices of the whole operating day. OMIE publishes cleared day-ahead prices the day before, so this is timestamp-legitimate for Spain. The NEM has **no day-ahead market**; AEMO pre-dispatch forecasts are non-binding and are not the realised RRP. For SA1/QLD1 the arm is a "next-24-hours-known" oracle, not a deployable day-ahead product. v10 relabels it and reports the Spanish case separately.

**A4 — RISK (temporal leakage in LOYO). ** Climatology planner inputs and policy tuning for the 2023 and 2024 folds use *later* price years (leave-one-year-out, not forward-chaining). This is valid cross-validation but not a causal forecast; the "other years" arm is therefore labelled F0 (acausal for early folds), and a causal previous-year arm F1 is added (not available for the 2023 fold). In addition, `fc_value` fell back to climatology (other years) for the first 7 days of the year in the rolling arms: a minor acausal fallback. v10 uses the realised history from day 1 (`roll_min_hist=1`); a unit test confirms no cleaning is possible on day 0 anyway.

**A5 — DEFECT (missing baseline). No forecast-matched price-aware threshold baseline.** `econ` uses a single production-weighted constant price `pbar`; the planner's gain over `econ` therefore confounds price awareness with the rest of the planner. v10 adds `ft`, a threshold rule with the same price/weather forecast, soiling estimate, contract, access, constraints, rain gate and packing as the planner, tuned on training data only.

**A6 — RISK (statistics). ** Real-market tables resample weather/dust replicates within only three price years per market; the reported ± intervals are conditional on those years and on the generator. Weather years (24) and dust draws are separate sources of variation from market years (3). Exact-benchmark percentages are ratios of means over 20 instances with sd comparable to the mean in the merchant 12 USD case (22 ± 12); no uncertainty was reported on "9 %".

**A7 — RISK (unused artefact). ** `results_exact_matched.json` (open-loop "matched" belief optimiser) knows future dust and rain; it was dropped from the paper but is still in the zip. v10 ships it flagged **not used**.

**A8 — RISK (reproducibility). ** Solver is `scipy.optimize.milp` (HiGHS bundled with SciPy 1.18.1), not Pyomo; no HiGHS version, thread count or hardware string recorded; raw AEMO CSVs not included; exchange rates fixed constants; clairvoyant gaps recorded (max 9.9e-5, all status 0) but not primal/dual bounds.

**A9 — RISK (scope). ** Exact instances: 6 rows, 60 days, 3 rows per mission; they say nothing about the 40-row annual problem. All soiling is generated.

**A10 — VERIFIED (positive checks from v9 code review).** `schedule_value` reproduces simulator net value to 1e-12; clairvoyant dominates all policies in every instance; MPC never exceeds the clairvoyant optimum (0 violations in 80 instances); default simulator outputs are unchanged by the v9 horizon keys; 10/10 tests pass on the shipped zip (re-run 2026-10-10).

## 6. Reproduction plan and limits

EXP-01 re-runs the complete v9 chain from the shipped code zip in a clean directory (about 45 min on 2 vCPUs) and compares every results file value-for-value with the shipped JSON. Outcome is appended in `docs/EXPERIMENT_LOG.md`. Where a number cannot be reproduced it is removed or marked in the manuscript. Nothing in v10 is tuned to improve reported performance; where corrected methods lower a v9 claim, the lower value is reported.
