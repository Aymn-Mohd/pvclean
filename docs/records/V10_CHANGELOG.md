# V10 changelog (methodology-correction release of E1)

## Corrections to v9 claims
1. **"9% matched-MILP" is a horizon effect, not an optimisation failure.** Merchant, 12 USD/row: 14-day horizon 1.97 USD vs 15.54 USD with 30 days and a 30-day tail (clairvoyant 21.58). In a deterministic world equal to the MILP's own model, 30- and 60-day variants equal the certified optimum on all 16 instances. See `OPTIMISATION_DIAGNOSTICS.md`.
2. **Terminology.** "Regret" is replaced by the clairvoyant-reference gap J* − J_π and the observed policy-performance difference J_MILP − J_π. The MILP is described as a benchmark under its own model, not an upper bound for deployable policies, and no information/optimisation split is claimed.
3. **Price-aware baseline added** (`ft`, forecast-matched threshold). It beats the planner under climatological forecasts (F0/F1) and on three of four small instances, ties under the export cap, and loses to the planner under F2/F3. The v9 statement that the planner's structure adds value is therefore qualified in the abstract, results and discussion.
4. **Forecast scenarios F0–F4 with decision timestamps** and an automated leakage test (23,562 checks, 0 failures). F0 and the tuning step are acausal for early folds; F3 is a day-ahead product only for Spain. Documented in `FORECAST_LEAKAGE_AUDIT.md` and `LIMITATIONS.md`.
5. **Statistics at the right level.** Generated markets: seeds are independent replicates. Real markets: three price years, intervals from resampling replicates within each year and conditional on those years; no cross-market generalisation is claimed. Paired bootstrap for planner-vs-ft.
6. **Forecast error vs value**: within-fold rank agreement 11/18 (3 expected by chance) but pooled Spearman −0.11 (p = 0.41, 54 pairs). Reported as "only partly predicts".

## Code
- New: `src/forecasting.py`, `src/optimisation.py`, `src/checks.py`, `src/evaluation.py`, `src/make_outputs_v10.py`, `src/claims_registry.py`, `experiments/*`, `tests/test_v10.py` (27 tests in total).
- Changed in `src/sim.py`: forecasts delegate to `forecasting.py`; decision log; `ft` policy; policy context. Regression: v9 numbers unchanged (EXP-01).

## Manuscript
- Rewritten: abstract, contributions, FT baseline, price-information scenarios, units, real-prices discussion, distance-to-optimum subsection (new Table III), discussion and limits. Regimes/sensitivity moved to `supplement.tex`. 6 pages.
- Removed from the paper to fit five pages: four context references (Wang 2022, Abdulla 2025, Zhang 2026, Kishor 2025, Gebhardt 2025) and several sensitivity sentences (still in the supplement or code results).

## Not done / open
- L2 (+next-24h prices) never cleans; its `dayahead` mode also swaps the rolling profile beyond 24 h. Reported, not investigated.
- Horizon table uses the transcribed <gpu-host> summary until the <gpu-host> `results_horizon.json` is dropped into `results/` (see `EXPERIMENT_LOG.md`).
- `\todo` placeholders: author emails, ARC co-author, funding, repository link. PES GM 2027 venue, deadline and page limit unverified. Three references were read as abstracts only. Cost assumptions need supervisor review.

## v10.1 (2026-10-16)
- Row-level sensing removed from E1 (moved to the sensing paper). The System Model describes the station regime only, and the supplement drops the value-of-information sentence.
- Horizon column of Table III verified against the <gpu-host> `results_horizon.json` (ANALYSIS check, verdict MATCH). The numbers are unchanged.
- Horizon column now computed directly from the full <gpu-host> `results_horizon.json` (680 runs). The output is byte-identical to the earlier transcription-based build, so the transcription dependency is closed.

## PES GM 2027 version (2026-10-23)
- Target: IEEE PES General Meeting 2027 (CFP: 5-page maximum, submission by 10 November 2026). The main text is now 5 pages.
- Title: "Contract-Aware Soiling Mitigation for Photovoltaic Plants Under Historical Electricity Market Prices".
- Author block: Ayman Mohammed Mohamed Rafiq, Mohamad Nassereddine; ARC co-author still a `\todo`.
- Energy framing: the abstract, introduction and discussion now lead with energy recovery and the value of a recovered MWh under each contract. Keywords are updated.
- New ANALYSIS metrics, post-processed from `results/results.json` with no new runs, in `src/make_outputs_pes.py`, which writes `paper/numbers_pes.tex` and `paper/table_rq1_pes.tex`:
  - recovered energy;
  - spread of recovered energy across policies;
  - revenue per recovered MWh;
  - specific yield gain;
  - export-cap energy loss.
  Energy differences between policies are descriptive (unpaired intervals).
- Table I has two energy rows.
- Cuts to reach 5 pages:
  - System Model detail condensed;
  - the condition-based and learned-schedule sentence dropped (3 fewer references);
  - experimental-design units shortened;
  - the MAE rank-agreement detail and the deterministic-check detail condensed.
- `main.tex` is now edited directly. `paper/build_main_v10.py` exits unless `--force` is given. The v10.1 text is kept as `paper/main_v10.1_frozen.tex`.
- 2026-10-23: removed ARC co-author and funding placeholders; authors are Ayman Mohammed Mohamed Rafiq and Mohamad Nassereddine.
