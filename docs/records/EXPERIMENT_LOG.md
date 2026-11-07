# Experiment log

## 2026-10-11 — v10 experiment run

Machine and versions: see `docs/REPRODUCIBILITY.md` (i7-13700HX, 24 logical CPUs, Python 3.13.16, SciPy 1.18.1).
Driver: `results/run_all.sh`. It runs the stages in order, skips a stage once `results/.stages/<stage>` exists,
and commits and pushes `results/` and `docs/` after each stage. It was launched detached with `setsid nohup`, with
the log in `results/log_run_all.txt`.

### Setup
- `uv`-managed CPython 3.13.16 venv at `.venv/`; installed numpy, pandas, scipy, pvlib, matplotlib, pytest.
- `cd tests && python -m pytest -q` → **27 passed** (10.3 s).
- `Pool(2)` → `Pool(os.cpu_count())` in `src/run_experiments.py`, `src/run_new.py`, `experiments/horizon_sensitivity.py`,
  `experiments/matched_information.py` (2 places), `experiments/price_aware_baseline.py` and
  `experiments/real_market_replay.py`. `import os` was added to the two `src/` files. No other code changes.
  (`experiments/forecast_audit.py`, `belief_world.py` and `reproduce_v9.py` use no pool.)

### Stages

| # | command (in `experiments/`) | start → end (+04:00) | outcome | log | output |
|---|---|---|---|---|---|
| 1 | `horizon_sensitivity.py` | 19:34:04 → 19:41:57 | 557 remaining runs completed; 680/680 present, unique keys; all solves status 0 | `log_horizon.txt` | `results_horizon.json` |
| 2 | `matched_information.py a` | 19:41:59 → 19:45:05 | 16 instances, all J* status 0 gap 0 | `log_matched_a.txt` | `results_matched.json` (`part_a`) |
| 3 | `matched_information.py b` | 19:45:06 → 19:45:08 | 4 settings tuned (seeds 1000–1004) and evaluated (0–19) | `log_matched_b.txt` | `results_matched.json` (`part_b`) |
| 4 | `price_aware_baseline.py` | 19:45:10 → 19:45:19 | 4 contracts, 50 test seeds | `log_price_aware.txt` | `results_ft_synthetic.json` |
| 5 | `real_market_replay.py` | 19:45:20 → 19:47:49 | 18/18 market×contract×fold keys | `log_replay.txt` | `results_replay.json` |
| 6 | `forecast_audit.py` | 19:47:51 → 19:47:54 | 23 562 checks, 0 failures | `log_forecast_audit.txt` | `results_forecast_audit.json` |

Stages 3–6 are fast because they run heuristic simulations only: one 40-row full-year simulation takes about
0.04 s. They were checked against their logs; each JSON holds the expected number of settings, seeds and keys.
The MILP stages (1, 2) are the expensive ones. `forecast_audit.py` prints `RuntimeWarning: Mean of empty slice` for
cells with no negative-price daylight hours; this is harmless (see FORECAST_LEAKAGE_AUDIT.md).

### Additional check (not in the run order): all-oracle MPC vs clairvoyant optimum

The brief stated that an all-oracle MPC arm reproduced the clairvoyant optimum (7.37 USD, seed 0). No stored file
contained the clairvoyant values for the horizon-study instances. They were therefore computed with the existing
`exact.solve` (same config as `horizon_sensitivity.py`, 120 s limit) and compared with the stored L7 arm. Output:
`results/check_L7_vs_clairvoyant.json`. The script was run from `src/` and is not part of the repository code:

```python
import sys, os, json
sys.path.insert(0, os.getcwd())
from multiprocessing import Pool
import sim, exact
def one(a):
    contract, crow, seed = a
    cfg = dict(sim.CONFIG); cfg.update(n_rows=6, night_min=100.0, d0=120, d1=180, c_row=crow)
    Rev = exact.row_tables(seed, contract, cfg); res, sched = exact.solve(Rev, cfg, 120)
    return dict(contract=contract, crow=crow, seed=seed, opt=exact.schedule_value(Rev, sched, cfg) - exact.schedule_value(Rev, [], cfg),
                status=int(res.status), gap=None if res.mip_gap is None else float(res.mip_gap))
if __name__ == "__main__":
    tasks = [(c, cr, s) for c, cr in [("fixed", 4.0), ("merchant", 12.0)] for s in range(20)]
    with Pool(os.cpu_count()) as p: out = p.map(one, tasks)
    h = json.load(open("../results/results_horizon.json"))
    l7 = {(x["contract"], x["crow"], x["seed"]): x["gain"] for x in h if x["arm"] == "L7 all of L1-L6"}
    for o in out: o["L7_gain"] = l7[(o["contract"], o["crow"], o["seed"])]; o["diff"] = o["L7_gain"] - o["opt"]
    json.dump(out, open("../results/check_L7_vs_clairvoyant.json", "w"), indent=1)
    for o in out: print(o["contract"], o["crow"], o["seed"], round(o["opt"], 2), round(o["L7_gain"], 2), round(o["diff"], 3), o["status"], o["gap"])
```

Result: seed 0 merchant/12 L7 = clairvoyant = 7.37 (confirmed). Exact match on 18/20 seeds (merchant/12) and
5/20 (fixed/4). L7 is never above the optimum, and the worst shortfall is 3.02 USD. All 40 clairvoyant solves had
status 0 and a gap ≤ 9.9e-5.

### Observations recorded during the run
- Key finding confirmed: deterministic belief world, merchant/12, days 120–180 — H14 = 0, J* = 20.40,
  H30 = H60 = 20.40.
- Information-ladder rung L2 (`price_mode="dayahead"`) never cleans in merchant/12 (0.00 on all 20 seeds). The
  `dayahead` mode also swaps the climatological price beyond 24 h for the rolling 28-day profile, so L2 is not a
  single-item rung. Not investigated further.
- The forecast-matched threshold (ft) beats the proposed planner on 3 of 4 small-instance settings, ties it in
  capped generated markets, and beats it under F0/F1 (climatological) forecasts in all six real-market cases
  except an ES PPA F1 tie.

### Not run in this session
- EXP-01 (`reproduce_v9.py`, full v9 chain re-run) and EXP-09, which `docs/V9_AUDIT.md` says will be logged here,
  were not part of this run order and have no new outcome.
- No paper text was changed.

## 2026-10-11 — cloud session (2 vCPU): EXP-01, EXP-09 and cross-machine check

- **EXP-01** (`experiments/reproduce_v9.py`, full v9 chain in a clean directory from the shipped v9 code zip): every re-run v9 result file is bit-identical to the shipped JSON except `results.json` field `runtime_s` (359 s vs 836 s, wall-clock only). 461 of 462 paper macros equal; the one difference is the same runtime figure. Output: `results/exp01_reproduce_v9.json`.
- **Cross-machine check**: forecast-matched threshold and real-market replay numbers computed on the cloud 2-vCPU container equal the GPU_HOST numbers (`results_ft_synthetic.json`, `results_replay.json`), as expected from per-run seeding.
- **Horizon study locally**: only 123 of 680 runs were completed in the cloud session (jobs were interrupted). The manuscript horizon column (Table III) therefore uses `results/horizon_summary_transcribed.json`, a transcription of the GPU_HOST `EXPERIMENT_RESULTS.md` values. `make_outputs_v10.py` switches to `results_horizon.json` automatically once it has at least 680 runs. Replace the local file with the GPU_HOST `results/results_horizon.json` and rerun `make_outputs_v10.py` to remove this dependency.
- **EXP-09** (`src/claims_registry.py`): `docs/CLAIMS_REGISTRY.md` lists all 140 numeric macros used in the paper and supplement and the file defining each. No undefined macro.
- **Tests**: 27 passed (`tests/`).
- **Manuscript**: `paper/main.tex` compiles to 6 pages with Fig. 1 in the main text (v9 layout kept), no undefined references. The regimes and sensitivity section is now a short paragraph in the paper and a full section with Fig. 1 in `paper/supplement.tex`.

## EXP-08 VoI sensing-quality sweep — smoke run only (2026-10-12, GPU_HOST, 24 logical CPUs)

Design: `docs/VOI_DESIGN.md`. Code: `src/voi.py`, `experiments/voi_sweep.py`, `tests/test_voi.py`.
`src/sim.py` change: one line, `cost_insp += cfg.get("insp_cost_scale", 1.0) * (c_mission + c_insp · n)`; the
default is bit-identical (tested), so no existing result changes. `docs/V10_CHANGELOG.md`, which the task brief named,
does not exist in the repository.

- Tests: `cd tests && python -m pytest -q` → 27 passed before any change; 37 passed after (10 new in `test_voi.py`).
- Smoke: `python experiments/voi_sweep.py --test-seeds 3 --out <scratch>/smoke_voi.json --log <scratch>/smoke_voi.txt`
  (all 102 arms × 4 contracts, full tuning on seeds 1000–1004, test seeds 0–2; 75 888 simulations, 377 s, 201 sims/s).
  Smoke output was written outside `results/` and is not committed.
- **Runtime estimate for the full sweep** (50 test seeds, 114 240 simulations): **≈ 9.5 min** on the GPU_HOST.
  Command: `python experiments/voi_sweep.py` → `results/results_voi.json`, `results/log_voi.txt`. **Not yet run.**

Smoke observations (3 seeds only; not results):
- Pipeline checks held on real runs: EVoI(station) = 0 exactly; σ = 0 / daily / free equals perfect information
  for both policies in all four contracts.
- `ft` under perfect row information lost ≈ 1 000–1 400 USD/yr versus `ft` under station information in every contract.
  Mechanism seen in the per-arm records: with row-level estimates rows cross the `ft` threshold on different nights and
  `ft` (no batching rule) dispatches ≈ 4× more missions (fixed: 197 vs 50 per year); under station information all rows
  share one estimate and are batched implicitly. The proposed planner (κ batching) did not show this. Per
  VOI_DESIGN.md §4 this is reported as an observed difference only, not as an information-vs-structure decomposition.

2026-10-16: moved out of E1 with the sensing paper scope change; code removed from e1-v10 and kept in main's history (94c699b).

## 2026-10-16: v10.1 changes
- ANALYSIS (not pre-registered): GPU_HOST horizon file check. `results/results_horizon.json` has 680 records, 0 duplicate keys and 36,856 solves, all with status 0. Its sha256 is `329c702d7208178f83af8d5fddee924223c682110ec8e8066de6e306741e783a`, and the file has been in git since commit 7076564. The check was committed as `1bcba4f` on `GPU_HOST-runs`. All 21 means used in Table III match the transcription to 2 dp; the largest unrounded difference is 0.0049. Verdict: MATCH. Table III numbers are unchanged, and `horizon_summary_transcribed.json` now records the check.
- Scope: row-level sensing (mobile and perfect information regimes, value of information, patrol cost) moves to the separate sensing paper. Two changes:
  - The supplement no longer has the "perfect row-level information is worth at most ... against a weekly patrol" sentence.
  - The System Model now describes the station regime only, which all E1 results use.
  - Main text: 6 pages, 0 undefined references, 0 overfull boxes. 137 macros, 0 unknown.
- Noted: the GPU_HOST repo (branch `GPU_HOST-runs`) does not contain the v10 code (`src/make_outputs_v10.py`, `src/claims_registry.py`, `experiments/`, `tests/test_v10.py`). Those files exist only in `E1_v10_research_code.zip` until they are committed.
- 2026-10-16, later: the full GPU_HOST `results_horizon.json` is now in `results/`. It came from the Mac upload of `origin/GPU_HOST-runs` at 1bcba4f, and its sha256 (329c702d...e783a) matches the manifest. It replaces the 123-run partial cloud file. `make_outputs_v10.py` now prints "horizon source: computed from results_horizon.json (680 runs)". `numbers_v10.tex` and `table_exact.tex` are byte-identical to the transcription-based build. The transcribed summary file stays as a record only.
- 2026-10-23: PES version. ANALYSIS energy metrics from existing RQ1 results (src/make_outputs_pes.py), no new runs. Main text 5 pages, 0 undefined references, 0 overfull boxes, 144 macros, 0 unknown.

---
## Phase R1 (2026-10-26), PRE-REGISTERED before any R1 run
Question: Under strictly chronological tuning and interval-level price valuation, does the contract-aware planner beat the forecast-matched threshold (FT) when both use the causal 28-day forecast F2?
Years:
- Australia (SA1, QLD1): season-aligned years without wrap-around. A1 = 1 Jul 2022 to 30 Jun 2023, A2 = Jul 2023 to Jun 2024, A3 = Jul 2024 to Jun 2025.
  Fallback if 2022 data can't be obtained: A2 and A3 only, with Jan to Jun 2023 as forecast warm-up.
- Spain: calendar 2023, 2024, 2025, with Dec 2022 as warm-up if available.
Protocol:
- Tune every policy (fixed, threshold, econ, FT, planner) on year 1 only, using the train seeds. Test year 2 with frozen parameters on the 50 test seeds.
- Year 3, primary: re-tune on years 1 and 2 (expanding window), then test. Year 3, secondary: year-1 parameters frozen.
- Pick the best conventional baseline by training mean only.
Forecasts:
- F2 is primary.
- Causal climatology is a sensitivity: the profile of the prior test years only.
- F3 (Spain day-ahead; Australia proxy) and F4 (oracle) are sensitivity only.
Primary metric: per test year, the seed-paired difference planner minus FT under F2 in net value (USD per year), with the mean and a 95% t-interval over the 50 seeds. Intervals are conditional on that price year; never pool years into one interval.
Cases: 3 markets x 2 contracts (merchant, PPA) x 2 test years = 12 case-years.
Hypothesis H-R1: the planner beats FT under F2.
Decision rule:
- SUPPORTED if the mean is above 0 in at least 10 of 12 case-years and no interval lies wholly below 0.
- NOT SUPPORTED if the mean is at or below 0 in at least 6 of 12.
- PARTIAL otherwise.
Secondary: planner minus the training-selected best baseline under F2, reported the same way (DESCRIPTIVE).
Sensitivity: Australia in the raw calendar with no season alignment, same protocol, labelled SENSITIVITY.
Not tested here: new markets, new soiling parameters, changes to the planner.
---

### Phase R1 results (2026-10-26, after the pre-registered runs)
- H-R1 verdict per the pre-registered rule: **PARTIAL**. Planner minus FT under F2: 11/12 case-year means > 0, 8/12 intervals wholly above 0, 1 wholly below 0 (ES merchant 2024: -74 USD/yr [-129, -20]).
- Secondary (DESCRIPTIVE): planner minus the training-selected best baseline 10/12 > 0 (7 above, 1 below); FT minus best baseline 6/12 > 0 (3 below).
- Sensitivity: CLIM planner-FT < 0 in 10/12; F3 and F4 > 0 in 12/12; Australia raw calendar 8/8 > 0 (all wholly above 0).
- 2022 AEMO (Jun-Dec) and OMIE Dec 2022 downloads succeeded; no fallback used. data/aemo_merged/ was not in the repo and was replaced by fresh AEMO downloads (provenance in data/provenance/r1_downloads.json).
- RQ1 rerun reproduces results.json rq1 inc_net to 7.3e-12.
- Deviations and full tables: docs/R1_SUMMARY.md.

---
## Phase R1b (2026-10-26), PRE-REGISTERED before any R1b robustness run
SENSITIVITY, generated markets, the same 50 test seeds, each variant retuned on the train seeds:
(a) no crop-access windows;
(b) station bias +25% and -25% on the measured soiling increment;
(c) cleaning effectiveness 0.98 instead of 0.995;
(d) continuous 3-year operation with the soiling state carried over and no clean reset (score years 2 and 3).
Comparisons: planner minus the training-selected best baseline (primary, matching the R1 secondary result) and planner minus FT.
Rule: a variant is ROBUST for a contract if the sign of the paired mean matches the default and, where the default interval excludes 0, the variant's interval does not lie wholly on the other side of 0. Otherwise it is NOT ROBUST. Report per contract.
---

### R1b blockers
- Stage 4: `results/results_matched.json` contains only `part_b`; the deterministic belief-world Part A table cited in
  `docs/OPTIMISATION_DIAGNOSTICS.md` is not in the stored file, so MILP_FORMULATION.md reports gaps from the stochastic
  instances only (results_exact.json, results_horizon.json, results_matched.json part_b). Not re-run (the brief asks for existing results).

### Phase R1b results (2026-10-26)
- Robustness (pre-registered rule): planner minus best baseline ROBUST in 19/20 variant-contract cells (NOT ROBUST: no access, capped);
  planner minus FT ROBUST in 14/20 (NOT ROBUST: no access fixed and PPA; bias -25% fixed and capped; cleaning to 0.98 capped; continuous capped).
- Claim recheck: 2 of 13 paper significance statements disagree with the stored intervals (price dip 31.7% merchant; NREL median merchant).
- Details: docs/R1_SUMMARY.md sections R1b.1-R1b.5 and deviations 16-25.

---
## Phase R2 (2026-10-28), PRE-REGISTERED before any R2 run
EXTENSION, generated markets, four contracts, the same 50 test seeds. Every policy is retuned on the train seeds for every setting, and the best baseline is selected on training data.
One factor varies at a time, the others stay at default:
- night window 240 / 360 (default) / 480 min;
- service time 15 / 25 (default) / 40 min per row;
- travel speed 0.25 / 0.5 (default) / 1.0 m/s;
- battery limit 6 / 10 / unlimited (default) rows per mission;
- availability 1.0 (default) / 0.9 / 0.8.
Metrics:
- value of cleaning: planner net value over no cleaning;
- planner minus the training-selected best baseline: paired mean and 95% t-interval;
- planner minus FT;
- recovered energy (MWh), row cleanings, missions.
Hypothesis H-R2: the planner's advantage over the best baseline is larger when robot capacity is tight (night 240 min, service 40 min, battery 6 rows) than at default.
Decision rule: per tight setting and contract, compare the paired difference in advantage (tight minus default, same seeds) against 0.
- SUPPORTED if it is positive with the interval above 0 in at least 6 of the 12 tight-setting-by-contract cells and below 0 in none.
- NOT SUPPORTED if it is at or below 0 in at least 6.
- PARTIAL otherwise.
DESCRIPTIVE: the value of cleaning against robot capacity, and the capacity at which the value of cleaning drops below 90% of default (the "sufficient robot" point) per contract.
---

### R2 blockers
- Step 3 of the brief says "13 settings x 4 contracts", but the pre-registered factor list has 11 distinct settings: the default plus 2 non-default levels of 5 factors (15 listed levels; the default is one setting, repeated in each factor). No reading gives 13. The sweep ran the 11 settings as pre-registered (44 cells); the pre-registration text does not state a count, so it is unaffected.

### Phase R2 results (2026-11-04)
- H-R2 per the pre-registered rule: **NOT SUPPORTED**. Difference in advantage (tight minus default) at or below 0 in 9/12 cells; 1 interval wholly above 0 (battery 6, PPA: +79 [+42, +115]), 5 wholly below 0. The verdict rests on reading "at or below 0" as the mean (R1 convention); counting intervals would give 5/12 and PARTIAL.
- Sufficient robot: not reached in the tested range in any contract; lowest value of cleaning 97.7% of default (battery 6, merchant).
- Unregistered diagnostics (results/r2_checks.json): verdict unchanged with 3 other train-seed sets; 90% point between 1 and 2 rows per mission; the robot uses about 9% of yearly night time.
- Details and deviations: docs/R2_SUMMARY.md.

---
## Phase R3 (2026-11-05), PRE-REGISTERED before any R3 run
MAIN-R3. The plant is placed in each price market with real local weather for the same years as the prices:
- SA prices: Adelaide (-34.93, 138.60), modules facing north;
- QLD prices: Brisbane (-27.47, 153.03), modules facing north;
- ES prices: Seville (37.39, -5.99), modules facing south.
Tilt is 25 degrees. Calendar years. Tune on 2023 and test 2024; retune on 2023 and 2024 and test 2025.
Weather: NASA POWER hourly for 2023 to 2025, the real weather of each year, on the price time base.
Production climatology for the planner and FT: the earlier NASA POWER years only (2001 to the year before the test year).
Dust and row noise: 50 replicate seeds per year. Intervals therefore reflect dust and noise only, conditional on that weather and price year.
Valuation: interval-level, as in R1. Forecast F2 is primary; causal climatology, F3 and F4 are sensitivity.
Soiling: default 0.30%/day is primary; 0.11%/day (NREL median of site means) is SENSITIVITY. Everything else is unchanged from R1.
Hypothesis H-R3: the planner beats FT under F2. Cases: 3 markets x 2 contracts x 2 test years = 12 case-years.
Decision rule:
- SUPPORTED if the mean is above 0 in at least 10 of 12 and no interval lies wholly below 0;
- NOT SUPPORTED if the mean is at or below 0 in at least 6 of 12;
- PARTIAL otherwise.
Secondary (DESCRIPTIVE): planner minus the training-selected best baseline, with the R1 decomposition into quantity and timing.
Not tested here: new markets, planner changes.
---

## R3 implementation notes (2026-11-05), committed before any R3 run
Choices the pre-registration leaves open, fixed here before step 4 so that no result can shape them.
1. Price series: SA1_raw, QLD1_raw, ES_raw (calendar years). R1's MAIN Australian series were the Jul-Jun aligned years, so the like-for-like R1 column for Australia is R1's SENSITIVITY raw-calendar series; the aligned R1 values are shown beside it.
2. Climatology: one per fold, 2001 .. test year - 1, used in tuning and at test. The tuning years are therefore inside the climatology, but the test year is not. Expected value (vexp) and the econ price come from the training price years, as in R1.
3. Production chain: the Dubai pipeline's (all-sky GHI, Erbs split, isotropic transposition, albedo 0.25, Faiman, gamma), not NASA's DNI and DHI. One change: Faiman takes hourly WS10M instead of the fixed 3 m/s, because R3 asks for real weather. The fixed-wind yield is reported.
4. Clocks: production is computed on the UTC clock with the sun at mid-hour, then moved to the price clock. NASA's HR stamp is the hour start (see data/provenance/r3_nasa_power.json). Daily rain sums the true hours of the local day, including 23- and 25-hour days.
5. 2001 east of UTC: the table starts at 00:00 UTC, so the first local hours of 2001 do not exist. They are NaN and nanmean drops them from the climatology. No simulated year is affected.
6. Interval wording: "dust and noise only" is slightly narrow. Everything seeded in R1 stays seeded, so intervals also reflect the seeded rain-forecast flags (hit and false-alarm draws). Real weather, prices and the row-exposure pattern are fixed.
7. 0.11 %/day: only soil_mean changes. season_amp stays 0.4, unlike R1's NREL "med" cell, which also used 0.16.
8. Left unchanged, as "everything else" says: the dust season peaks mid-June by calendar day, which is winter in Adelaide and Brisbane; storm timing; blackout days 60, 150, 300. This is a limit of R3, not a site calibration.
9. Y3frozen (R1 secondary) is not pre-registered for R3 and is not run. F3 stays a realised-price proxy in Australia, as in R1.
10. results/results_matched.json already holds v10 `part_b`, read by src/make_outputs_v10.py, experiments/milp_gaps.py and experiments/failure_diag.py. R3 adds the keys `r3` and `r3_meta` to that file and keeps `part_b` unchanged.

### R3 blockers
None. All 75 NASA POWER files downloaded.

### R3 results (2026-11-05)
MAIN-R3: H-R3 is NOT SUPPORTED by the rule. Mean above 0 in 6 of 12, at or below 0 in 6; 5 intervals wholly above 0 and 5 wholly below. The label depends on QLD merchant 2025 (-6 USD/yr, 46 of 50 seeds tied); a positive mean there would give PARTIAL. SENSITIVITY 0.11 %/day: NOT SUPPORTED, 3 of 12.
By site: Seville 4 of 4 positive, Brisbane 0 of 4, Adelaide 2 of 4 (2024 positive, 2025 negative). Full tables: docs/R3_SUMMARY.md.
UNREGISTERED DIAGNOSTICS (experiments/r3_checks.py, results/r3_checks.json; no effect on the verdict): the 6 losses are the 6 case-years with the planner below no cleaning; kappa is at the grid top in 12 of 12; moving the dust and storm seasons 182 days gives 5 of 12 and keeps the Seville and Brisbane signs; three other train-seed sets keep all 12 signs. Adelaide's NASA POWER rain looks low and has not been compared with gauges.
`src/sim.py` gained `season_shift` (opt-in, off by default) for the diagnostics, after the replay. Two stored cases reproduce exactly with it in place.

---
## POST HOC after R3
Question: is the planner's over-cleaning in R3 a limit of its kappa grid? Change: kappa grid {0, 0.5, 1, 2} -> {0, 0.5, 1, 2, 4, 8, 16, 32}. Everything else as in R3 (0.30%/day, F2). Label: POST HOC; the R3 verdict is unchanged.

---
## Phase R3b (2026-11-05), PRE-REGISTERED before any R3b run
ANALYSIS: compare NASA POWER daily rain with gauge rain at the three R3 sites for 2023 to 2025. Report annual totals and the counts of days >= 5 mm and >= 1 mm.
SENSITIVITY: if a site's gauge count of days >= 5 mm differs from NASA POWER by more than 25% in any test year, rerun that site's R3 cases with gauge daily rain in place of NASA POWER rain.
Everything else as in R3: R3 kappa grid, 0.30%/day, F2.
Report planner minus FT and planner minus the training-selected best baseline. Label: SENSITIVITY; the R3 verdict is unchanged.
---

### R3b blockers
All three gauge sources failed on 2026-11-05, so R3b has no gauge data. One request per URL, User-Agent `e1-r3b-research-client`, no retries and no workaround. URLs and reply hashes: `data/provenance/r3b_gauges.json`.
1. BoM, Adelaide (Kent Town) 023090 and Brisbane 040913: Climate Data Online returned HTTP 403 for both stations: "Your access is blocked due to the detection of a potential automated access request. The Bureau of Meteorology website does not support web scraping: if you are trying to access Bureau data through automated means, you should stop." Adelaide and Brisbane are skipped, as the brief says. The reply offers an anonymous FTP channel and a Registered User service; neither was tried. No other station was tried: the fallback covers gaps above 5%, and a station's gaps cannot be measured without its data.
2. AEMET, Sevilla Aeropuerto 5783: the OpenData daily endpoint returned HTTP 200 with an empty body when no API key is sent, and the portal issues API keys through registration. Seville is skipped, as the brief says. No key was requested.


---
## Phase R4 run log (2026-11-07)
Pre-registration: docs/records/decisions.md, "Phase R4", committed alone as 177ff66 before any R4 simulation. Inputs commit 94389da.
Runs, in order, 24 workers, nice 10: r4_sites, r4_kappa, r4_shift, r4_lowsoil, r4_cost, r4_seeds. All rc 0; user CPU 9477 s (2.63 h). Times: results/time_r4_*.txt.
Deviations and fixes:
1. Downloaded 2001 to 2025 for each new site, not 2023 to 2025: the R3 climatology and read_power need those years. 125 requests, one each, all HTTP 200, client pvclean-research-client.
2. `pvclean download` gained `--sites`: a failed site is dropped and the next continues; HTTP 403 or 429 stops the run. tests/unit/test_download.py expected 75 NASA targets; it now expects 200.
3. site_wx.npz was rebuilt with the five new tables. The R3 arrays are bit-identical (checked with numpy array_equal); the file's sha256 changed. The R3 file is kept at HOME_DIR/backups/pvclean/site_wx_r3.npz.
4. The brief names decisions.md for the pre-registration; CLAUDE.md names this log. The entry is in decisions.md, as the brief says, and this log points to it.
5. R4 scripts live in src/ and paper/, as the brief says; the package layout has neither directory otherwise.
6. Rule order: DESCRIPTIVE tested first (implementation note 1). It did not matter: both sides have at least 4 case-years.
7. Dubai marker: the 12 R1 case-years on the raw price series, not R1's MAIN aligned series (implementation note 11). Both values are in docs/R4_SUMMARY.md section 7.
8. Figure additions not in the brief: marker shape shows the contract, merchant and PPA are moved 1.2 days apart so that they do not overprint, and the band is labelled "no prediction".
9. Added after seeing results, labelled POST HOC: the by-contract table, the "how firm the label is" line, the new-sites-only count, and the rule column, which is not a verdict.
10. src/make_r4_summary.py: fixed a keyword clash in dubai() on its first real run. No result changed.


---
## Phase R5 run log (2026-11-07)
Pre-registration: docs/records/decisions.md, "Phase R5", committed alone as 37f1aa2 before any R5 simulation. Inputs commit 2721808.
Runs, in order, 24 workers, nice 10: r5_merchant, r5_ppa, r5_kappa. All rc 0; user CPU 3027 s (0.84 h). Sanity script: 335 s more.
Deviations and fixes:
1. The pre-registration added one DESCRIPTIVE line the brief did not ask for: the count without Whyalla, because its rain tracks Port Augusta (note 3). The verdict uses all sites.
2. site_wx.npz was rebuilt with six more tables. The eight earlier site tables are bit-identical. The previous file is kept at HOME_DIR/backups/pvclean/site_wx_r4.npz. tests/unit/test_download.py now expects 350 NASA targets.
3. tests/regression/test_r5_jobs.py simulates, so it stayed out of git and out of the suite run until the pre-registration was pushed. That one suite run therefore had 354 tests, without it.
4. src/r5_sanity.py is POST HOC and was not in the brief: same-seed and input checks, every point of the R3 planner grid at Whyalla and Port Augusta 2024 merchant, and retuning on three other train-seed sets. It found no fault. It did not isolate why the two sites differ.
5. src/make_fig_r4.py: legend now reads R3 sites, R4 sites, R5 sites; the contract keys are grey-filled, so that half-filled means R5. The script now needs the R5 results, so the v1.1.0 public copy differs from this one.
6. src/make_r4_summary.py is unchanged and is imported by the R5 scripts.
