# Changelog

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

- First public release, for the paper "Contract-Aware Cleaning Gains Track Dry Spells", submitted to IEEE PES General Meeting 2027.
- The package, study configs, tests, documentation, stored results and generated paper macros and tables.
- No market or weather data is included.
