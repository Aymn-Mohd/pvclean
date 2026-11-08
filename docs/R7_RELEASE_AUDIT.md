# Release audit for Phase R7 (2026-11-08)

Question: which public pvclean release (v1.1.0, v1.2.0, v1.3.0, at github.com/Aymn-Mohd/pvclean) holds code and configs that reproduce R3, R4, R5 and R6 exactly, and what v1.3.0 contains. Nothing public was changed.

## Method

Each tag was extracted with `git archive` and its `pvclean/`, `configs/`, `src/` and `scripts/` compared file by file (`diff -rq`) with this repository at commit 549df24, the last commit before any R7 code. This repository's code reproduced the stored R3 and R4 planner-minus-FT means exactly (R6 job r6_seeds: largest difference 0.0 USD), and the stored plain-threshold parameters and nets of all 56 case-years exactly (R6 job r6_plain). Data files read by one matched-site job were traced: only `real_prices_v2.npz` and `site_wx.npz`. No release contains data. Both files are rebuilt from public downloads (`pvclean.markets.build` from the AEMO and OMIE files; `pvclean download nasa-power` and `pvclean.weather.build`). The older `real_prices.npz`, which cannot be rebuilt, is not read by R3 to R6.

## Differences from the code that produced the results

| release | differs in | effect on R3 to R6 |
|---|---|---|
| v1.1.0 | no R5 or R6 configs or modules; R5 sites absent from `download.py`, `sites/__init__.py`, `weather/build.py` (additions only); `src/make_fig_r4.py` without the R5 points; version string; one redacted file name in two reporting modules | none for R3 and R4 |
| v1.2.0 | no R6 configs or modules (`r6.py`, `exact/oracle.py`, `policies/replay.py`, R6 rules and `nested_bootstrap`; additions only); version string; the same redaction | none for R3 to R5 |
| v1.3.0 | version string; the same redaction (`horizon_summary_transcribed.json` for the private file name, in `reporting/claims_registry.py` and `reporting/numbers_v10.py`) | none |

## Answer

| phase | v1.1.0 | v1.2.0 | v1.3.0 |
|---|---|---|---|
| R3 (matched sites) | yes | yes | yes |
| R4 | yes | yes | yes |
| R5 | no (no R5 code, configs or sites) | yes | yes |
| R6 | no | no | yes, with the caveat below |

"Yes" means the study code and configs are byte-identical to the code that produced the stored results, apart from additions and the redaction above. It was established by comparison, not by rerunning each tag; the rerun evidence is for this repository's code, which equals v1.3.0. v1.1.0's `src/make_fig_r4.py` draws the R4 figure as it was in R4; later releases also plot the R5 points.

R6 caveat: the stored `results_r6_oracle.json` includes the post-run fix of the oracle re-solve step (24 units below the 1,000 USD/yr cut; EXPERIMENT_LOG "Phase R6 run log", item 2). v1.3.0 holds the fixed code and `scripts/r6_resolve_oracle.py`. A fresh `r6_oracle` run with v1.3.0 code takes the fixed re-solve path inside the job, so it should give the stored values directly; this was not checked by a full rerun (about 200 CPU hours).

No release contains R7: the R7 code (commit 426446e onward) is private until a later release.

## What v1.3.0 contains

Tag v1.3.0, commit 962ef53, release asset `pvclean-1.3.0.zip` (`git archive` of the tag).
- The `pvclean` package: simulator, policies (including the schedule replay), forecasts F0 to F4, markets, contracts, sites (all 14 matched sites), weather and data builders, the exact benchmarks (subset MILP, receding horizon, the full-year oracle with its Lagrangian bound), statistics and decision rules through R6, study runners through R6, reporting.
- Study configs through R6 (`configs/studies/r6_oracle.yaml`, `r6_plain.yaml`, `r6_seeds.yaml` and all earlier ones).
- Stored results JSON through R6, including `results_r6_*.json` and `r6_sanity.json`; the paper macros and tables in `papers/e1_pes/`.
- Summaries `docs/R4_SUMMARY.md`, `R5_SUMMARY.md`, `R6_SUMMARY.md`; records in `docs/records/` (pre-registrations, decisions through the R6 results, experiment log through the R6 run log, `REDACTIONS.md`).
- Scripts `src/make_r4_summary.py`, `make_fig_r4.py`, `r4_sanity.py`, `make_r5_summary.py`, `r5_sanity.py`, `make_r6_summary.py`, `make_fig_r6.py`, `make_r6_sanity.py`, `scripts/r6_resolve_oracle.py`.
- Tests (unit, regression, smoke, extension; 250 pass and 17 skip without data), `README.md`, `CHANGELOG.md`, `CITATION.cff` (paper "Price Forecasts Add Little to PV Cleaning Rules", submitted to IEEE PES General Meeting 2027), `LICENSE` (MIT).
- Not included: data, PDFs and figure PNGs, the `legacy/` code and tests, the manuscript sources, run logs and timing files.

Note added for release v1.4.0: the commit hashes above (549df24, 426446e) are in the private development repository, from which each release is exported. v1.4.0 publishes the R7 code, configs and results.
