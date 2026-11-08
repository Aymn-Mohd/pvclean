# Changelog

## 1.4.1 (2026-11-08)

- `docs/ORACLE_BOUND.md`: how the oracle repairs an over-full night (removed rows are barred from that night) and why its Lagrangian bound with the K-row night cap bounds every feasible schedule, from `pvclean/exact/oracle.py` only.
- `data/provenance/NLR.md`: the NLR file hashes, the earliest record of their download, and download instructions for AEMO, OMIE (`marginalpdbc`) and NASA POWER (hourly point API, community RE, UTC).
- `docs/records/decisions.md`: an index of phases R3 to R7, with where each was defined and the commits that registered and reported it.
- README: one command that rebuilds Tables I and II and the figures from the stored results.
- No code, config or result file changed.

## 1.4.0 (2026-11-08)

- Sensitivity runs (Phase R7, no decision rules): price forecasts F2, F7d, F56d, FHW, F3 and F4; a planner that may abstain (kappa up to inf); dust rates; rain cleaning effectiveness; cleaning costs; and an oracle split that removes one kind of information at a time (rain, prices, per-row soiling). Studies `r7_forecast`, `r7_abstain`, `r7_dust`, `r7_rain`, `r7_cost` and `r7_oracle_split`, in `pvclean/studies/r7.py`.
- Forecast FHW (`pvclean/forecasts/roll_hw.py`): the 28-day rolling hour-of-day mean taken separately over past weekdays and weekend days. The other forecasts are unchanged.
- Oracle (`pvclean/exact/oracle.py`): optional rain, price and station-soiling inputs, so it can plan on restricted information. The defaults reproduce R6.
- Statistics: `cluster_median_ci`, a cluster bootstrap interval of a median.
- Results: the `results/results_r7_*.json` files, `results/r7_sanity.json` and `results/r7_fig_axes.json`. `docs/R7_SUMMARY.md` reports them; `docs/R7_RELEASE_AUDIT.md` says which release reproduces R3 to R6.
- Scripts: `src/make_r7_summary.py`, `src/make_fig_r7.py` (`paper/fig_policies.pdf`) and `src/make_r7_sanity.py`.
- Records: the R7 definitions in `docs/records/decisions.md` and the R7 run log in `docs/records/EXPERIMENT_LOG.md`.
- The README maps every paper table and figure to its config and commands, and gives the compute cost of the R7 oracle split (about 60 CPU hours).
- `CITATION.cff`, the README and the 1.0.0 entry below: new paper title "Causal Price Forecasts Add Little to PV Cleaning".
- Stored results used by the paper macros are unchanged.

## 1.3.0 (2026-11-08)

- Perfect-foresight benchmark: `pvclean/exact/oracle.py` finds a feasible full-year schedule with known prices, rain and dust, under the same robot, night budget, access windows and costs, and a Lagrangian upper bound. `pvclean/policies/replay.py` scores a schedule in the simulator.
- Studies: `r6_oracle`, `r6_plain` and `r6_seeds`, in `pvclean/studies/r6.py`. Statistics: `headroom_rule`, `ft_plain_rule` and `nested_bootstrap`.
- Results: the `results/results_r6_*.json` files and `results/r6_sanity.json`. `docs/R6_SUMMARY.md` applies the two pre-registered rules over 56 case-years. Both verdicts are NOT SUPPORTED: FT reaches 90% of the oracle value in 16 of 30 case-years worth at least 1,000 USD/yr, and beats the plain loss threshold in 7 of 14 merchant case-years.
- One fix after the R6 run, in the oracle's re-solve step, is described in `docs/records/EXPERIMENT_LOG.md`, "Phase R6 run log". `scripts/r6_resolve_oracle.py` reruns the affected units.
- Scripts: `src/make_r6_summary.py`, `src/make_fig_r6.py` and `src/make_r6_sanity.py`. Figures are written to `paper/`, which git ignores.
- `CITATION.cff`, the README and the 1.0.0 entry below: new paper title. The README now gives the compute cost of the benchmark.
- Stored results used by the paper macros are unchanged.

## 1.2.0 (2026-11-07)

- Sites: Murcia, Badajoz, A Coruña, Whyalla, Mount Gambier and Roma, with the same plant and tilt rules as the matched sites.
- Studies: `r5_rain`, `r5_merchant`, `r5_ppa` and `r5_kappa`, in `pvclean/studies/r5.py`.
- Results: `results/r5_rain.json`, the `results/results_r5_*.json` files and `results/r5_sanity.json`. `docs/R5_SUMMARY.md` applies the pre-registered rule for merchant contracts at unseen sites. Its verdict is NOT SUPPORTED: 5 of 10 predicted case-years.
- Scripts: `src/make_r5_summary.py` and `src/r5_sanity.py`. `src/make_fig_r4.py` now also plots the R5 points and needs the R5 results.
- The new downloads are recorded in `data/provenance/r5_nasa_power.json`.
- `CITATION.cff` and the README: new paper title and author list. The 1.0.0 entry below now uses the new title.
- Stored results used by the paper macros are unchanged. `docs/records/REDACTIONS.md` lists one new replacement.

## 1.1.0 (2026-11-07)

- Sites: Almería, Córdoba, Bilbao, Port Augusta and Longreach, with the same plant and tilt rules as the matched sites.
- Studies: `r4_rain`, `r4_sites`, `r4_kappa`, `r4_shift`, `r4_lowsoil`, `r4_cost` and `r4_seeds`, in `pvclean/studies/r4.py`.
- Results: the `results/results_r4_*.json` files, `results/r4_rain.json` and `results/r4_sanity.json`. `docs/R4_SUMMARY.md` applies the pre-registered dry-spell rule. Its verdict is PARTIAL.
- Scripts: `src/make_r4_summary.py`, `src/make_fig_r4.py` and `src/r4_sanity.py`. The figure and trace PNG are written to `paper/`, which git ignores.
- `pvclean download nasa-power --sites <names>` fetches only those sites. The new downloads are recorded in `data/provenance/r4_nasa_power.json`.
- Statistics: `dry_rule`, `dry_prediction` and `cluster_spearman`.
- Stored results used by the paper macros are unchanged. `docs/records/REDACTIONS.md` lists one new replacement.

## 1.0.1 (2026-11-06)

- Tests: `test_files_found` checks tracked files only, so it passes after `pvclean report` has run in the same folder.
- Tests: new `tests/test_report_then_suite.py` runs `pvclean report` and then the full suite in one folder.
- `.gitignore`: added the files `pvclean report` writes, `papers/e1_pes/table_real.tex` and `results/figures/`.
- `CITATION.cff`: added a contact entry. The README and `docs/DATA.md` now point to it for `real_prices.npz`.
- Placeholders: `GPU_HOST`, `HOME_DIR` and `GH_USER` replace the angle-bracket forms, which GitHub hid in rendered Markdown.
- Records: removed a general working-practice document and every reference to it.
- Records: removed the mentions of a prospective co-author who is not on the paper.
- `docs/records/REDACTIONS.md` lists both records changes.

## 1.0.0 (2026-11-06)

- First public release, for the paper now titled "Causal Price Forecasts Add Little to PV Cleaning", submitted to IEEE PES General Meeting 2027.
- The package, study configs, tests, documentation, stored results and generated paper macros and tables.
- No market or weather data is included.
