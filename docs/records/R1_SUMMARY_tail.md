## 8. Deviations from the pre-registration and other protocol notes

1. **Run mode.** The task started in SLICE mode (WINDOW_END printed as 2026-10-26 11:45 +04). Mid-session the user lifted the
   time limit ("its fine no time limit"). Every job finished anyway (replay wall time 4 min 22 s), so nothing was skipped.
2. **Australian data source.** `data/aemo_merged/` named in the brief does not exist in this repo. The 5-min RRP files were
   downloaded from AEMO's aggregated price-and-demand CSVs for Jun 2022 to Dec 2025, SA1 and QLD1 (86 files; URLs and sha256 in
   `data/provenance/r1_downloads.json`; raw files are git-ignored under `data/raw/`). The 2022 download succeeded, so **the
   pre-registered fallback was not needed**: A1, A2 and A3 are all used. As a cross-check, hourly means of the new downloads
   reproduce the old `data/real_prices.npz` `*_raw` arrays (2023-2025) to at most 1.8e-15 USD/kWh.
3. **Extra warm-up month.** The pre-registration names a Spain warm-up (Dec 2022) but none for A1. Jun 2022 was also downloaded
   so that F2 has its 28-day history from the first day of A1 (training year only). Jun 2022 contains AEMO's market suspension
   and administered pricing (mid-Jun 2022). It affects only the F2 forecast for the first 28 days of the A1 training year.
4. **Spain Dec 2022 warm-up.** The day files are not served individually for 2022. The OMIE yearly archive
   `marginalpdbc_2022.zip` was downloaded (URL and sha256 in provenance) and the 31 December members were used. **This download
   succeeded.**
5. **Regression test (d), bit-identity.** The old hourly-mean arrays pushed through the new code path reproduce SA1 merchant
   fold 0 (F2: tuned parameters and all 50 seeds of planner and FT) bit-identically **against the unchanged v10 code path run in
   this environment**. Against the stored `results/results_replay.json` they agree to at most 2.2e-11 USD per seed, not
   bitwise. The unchanged v10 code path shows the same 2.2e-11 difference, so the stored file comes from an earlier numeric
   environment. The test asserts bit-identity to the v10 path and atol 1e-9 to the stored file.
6. **CLIM tuning.** For the year-1 fold there are no prior years. As in the v10 replay, tuning uses the month x hour profile of
   the training years themselves (in-sample), and the test uses the profile of the prior years only (causal). In Y3 the training
   profile covers years 1+2.
7. **F3 for Australia** is a proxy: the realised 5-min operating-day values are revealed one day ahead. The NEM has no
   day-ahead auction, so this is a strong proxy close to an oracle for the first 24 hours.
8. **Y3frozen** freezes the year-1 parameters *and* the year-1 planner inputs (production climatology, value profile, econ
   price).
9. **Training-seed split in Y3.** The five train seeds (rx.TRAIN 1000-1004) map to training years by seed mod 2, so three seeds
   use year 1 and two use year 2. This is the v10 convention for multi-year training.
10. **Tie-breaking.** Ties in training mean are broken by first position in the grid, as in `rx.tune`. A first replay launch
    that used a different tie rule was stopped early and its partial output deleted before any result was used. The reported run is a
    clean rerun.
11. **Best baseline in the RQ1 decomposition.** It is selected by training mean, as pre-registered for R1. For the fixed
    contract this gives threshold; `results.json` stores econ, which it selected on the test mean.
12. **Spain DST and quarter-hour days.** Fifteen-minute days (92, 96 or 100 periods) are grouped by 4 consecutive periods. The
    23-hour and 25-hour days are then resampled linearly to 24 positions, as in `build_new.py`, applied to each hourly field.
13. **Decomposition reference value.** v_ref is defined per seed-year as sum_h pdc_h v_h / sum_h pdc_h, using the clean-plant
    production profile of that seed's weather, so it is policy-independent.
14. **Raw-calendar sensitivity verdict.** The SUPPORTED/NOT SUPPORTED rule is for 12 case-years, so it is not applied to the
    8 sensitivity case-years; only counts are reported.
15. **Worker count.** Pool(os.cpu_count() = 24). ES merchant Y2 was rerun with Pool(3) and is bit-identical in every policy,
    forecast and seed.

### R1b deviations and protocol notes

16. **Per-seed reruns for the claim recheck.** `results.json` price and `results_extra.json` cost store only paired summaries. These
    14 settings were rerun with per-seed storage (same grids, seeds and tuning) and reproduce the stored paired means to at most
    3.5e-12 USD. `results_wx.json` and `results_nrel.json` were used as stored.
17. **Comparator in the claim recheck.** The paper's figures use the best baseline chosen on the test mean, so the recheck does
    too. The training-selected comparison is shown alongside. The Wilcoxon test is two-sided signed-rank with zero differences
    dropped (SciPy default). "excludes 0" refers to the 95% t-interval.
18. **Robustness default.** The default is the RQ1 rerun with per-seed storage (`results_rq1_decomp.json` rq1). It uses the same
    policies (fixed, threshold, econ, FT, planner), the same tuning and a training-selected best baseline. The pre-registration
    does not name the default's source.
19. **Variant (b).** The bias is applied to the station's measured site increment in the estimate update. The true soiling is
    unchanged. Only station information is used, as in RQ1.
20. **Variant (c).** clean_residual = 0.02 applies to both the true cleaning and the planner's or FT's model of a cleaned row:
    the policies know the effectiveness.
21. **Variant (d), continuous operation.**
    - Year k of chain s uses seed s + 10000 k (k = 0, 1, 2). Train chains use 1000-1004 the same way; no seed collides with the
      test, train or planner-input seeds.
    - The planner and FT horizons wrap into the next year's climatology (`wrap_horizon`); in single-year runs they are truncated
      at day 364. The rain gate and the access look-ahead do not wrap. There is no access window near the year end, and on
      day 364 the rain gate sees 1 day.
    - The no-cleaning reference chain is carried over in the same way. Tuning uses the same year-2-3 score.
22. **Worker count, R1b.** Two robustness cells (d capped, b +25% PPA) were rerun with Pool(3) and are bit-identical to Pool(24).
23. **Exact benchmark documents.**
    - Built from stored results only.
    - `results_matched.json` lacks the Part A belief-world table cited in OPTIMISATION_DIAGNOSTICS.md (logged under "R1b
      blockers").
    - Clairvoyant solve times are not stored.
24. **Diagnostics.**
    - `sim.simulate` gained an opt-in `cfg diag` per-day log. Reruns with it reproduce the stored per-seed nets exactly.
    - Diagnostic (b) compares the planner with FT and with the clairvoyant J\* schedule, valued on the same revenue table (the
      planner's table value equals its simulated gain to 2e-13).
    - The palette validator from the plotting guide could not run (no Node.js on this machine). The figures use the reference
      palette's first three categorical slots in fixed order, plus line-style encoding.
25. **Corrected commit.** The first stage-5 commit (5daa129) contained an inaccurate diagnostic write-up: the trajectory
    description, the index mechanism and the rain days. It was corrected in aa489ce; no history was rewritten.

## 9. Reproduction

```bash
cd src && ../.venv/bin/python real_prices_v2.py           # needs data/raw/ (see data/provenance/r1_downloads.json)
../.venv/bin/python price_audit_r1.py
cd ../experiments && ../.venv/bin/python chrono_replay.py  # results/results_chrono.json, log results/log_chrono.txt
../.venv/bin/python rq1_decomp.py                          # results/results_rq1_decomp.json (stops if RQ1 is not reproduced to 1e-6)
../.venv/bin/python sanity_tau.py                          # results/results_sanity_tau.json
cd ../src && ../.venv/bin/python make_r1_summary.py        # this file
cd ../experiments && ../.venv/bin/python claims_recheck.py  # R1b: results/claims_recheck.json
../.venv/bin/python robustness.py                         # R1b: results/results_robust.json
../.venv/bin/python milp_gaps.py                          # R1b: results/milp_gaps.json
../.venv/bin/python failure_diag.py                       # R1b: results/failure_diag.json, results/figures/r1b_diag_*.pdf
cd ../src && ../.venv/bin/python provenance_r1b.py        # R1b: data/provenance/NLR.md, results/audit_counts.json
../.venv/bin/python make_r1_summary.py
cd ../tests && ../.venv/bin/python -m pytest -q            # 37 tests
```

CPU time (user): replay 2,873 s; RQ1 rerun and decomposition 204 s; price build, audit, sanity check and tests under 2 min.
R1b CPU time (user): claim recheck 371 s (wall 31 s), robustness 980 s (wall 59 s); diagnostics, worker checks, MILP
gaps, provenance and tests about 5 min in total. CPU only; no GPU code paths exist.
