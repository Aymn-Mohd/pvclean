# Changelog

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
