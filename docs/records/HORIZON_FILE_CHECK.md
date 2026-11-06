# Horizon file check: results/results_horizon.json

**ANALYSIS (not pre-registered).** This is a file-integrity and transcription check. No experiment, solver or GPU job was run.

- Date: 2026-10-16 (<gpu-host>, <gpu-host>)
- Path: `results/results_horizon.json` (the only copy under `~`; `find ~ -name results_horizon.json -not -path "*/.cache/*"`)
- Size: 288 851 bytes; mtime 2026-10-11 19:41:57 +0400 (end of the `horizon_sensitivity.py` run in EXPERIMENT_LOG.md)
- sha256: `329c702d7208178f83af8d5fddee924223c682110ec8e8066de6e306741e783a`
- Git: the file was already tracked (commit 7076564, "Results: 1_horizon"); the working copy is identical to HEAD.

## Validation

| Check | Result |
|---|---|
| Records | 680 (required: 680) |
| Unique (contract, crow, seed, arm) keys | 680; 0 duplicates |
| Required fields contract, crow, seed, arm, gain | present in all 680 records |
| Status field | `status_counts` (dict per record): 36 856 solves in total, all status `0`; no other status value |
| Other solver fields | `no_solution` sum = 0; `viol` sum = 0; largest `max_gap` = 0.00100 (tolerance 1e-3) |
| Seeds | 0 to 19 (20 per setting and arm) |

Keys present: contract, crow, arm, seed, gain, n_clean, n_missions, runtime, n_solves, max_solve_s, status_counts,
max_gap, no_solution, first_obj, first_bound, viol, final_sr_mean, final_sr_min.

Arms (sorted): H07, H14, H14+T16, H30, H30+T30, H60, L1 +row exposure, L2 +next-24h prices, L3 +all prices,
L4 +future dust, L5 +future weather, L6 +true row state, L7 all of L1-L6.

Records per (contract, int(crow)): fixed|4 = 220 (5 H arms + L1, L3 to L7), fixed|12 = 100 (5 H arms),
merchant|4 = 100 (5 H arms), merchant|12 = 260 (6 H arms incl. H60 + L1 to L7).

## Comparison with the values in docs/OPTIMISATION_DIAGNOSTICS.md

Mean gain (USD) per (`f"{contract}|{int(crow)}"`, arm) by `np.mean` over the 20 seeds. The arm names in the file
are the same as the transcribed names, so no mapping was needed. The ladder arms (L1 to L7) have no transcribed
values and are not compared.

| setting | arm | n | recomputed | transcribed | abs diff |
|---|---|---|---|---|---|
| fixed|4 | H07 | 20 | 127.33 | 127.33 | 0.000 |
| fixed|4 | H14 | 20 | 141.82 | 141.82 | 0.000 |
| fixed|4 | H14+T16 | 20 | 144.57 | 144.57 | 0.000 |
| fixed|4 | H30 | 20 | 145.86 | 145.86 | 0.000 |
| fixed|4 | H30+T30 | 20 | 147.38 | 147.38 | 0.000 |
| fixed|12 | H07 | 20 | 2.44 | 2.44 | 0.000 |
| fixed|12 | H14 | 20 | 75.67 | 75.67 | 0.000 |
| fixed|12 | H14+T16 | 20 | 81.69 | 81.69 | 0.000 |
| fixed|12 | H30 | 20 | 81.73 | 81.73 | 0.000 |
| fixed|12 | H30+T30 | 20 | 81.36 | 81.36 | 0.000 |
| merchant|4 | H07 | 20 | 14.14 | 14.14 | 0.000 |
| merchant|4 | H14 | 20 | 61.96 | 61.96 | 0.000 |
| merchant|4 | H14+T16 | 20 | 63.15 | 63.15 | 0.000 |
| merchant|4 | H30 | 20 | 63.14 | 63.14 | 0.000 |
| merchant|4 | H30+T30 | 20 | 62.93 | 62.93 | 0.000 |
| merchant|12 | H07 | 20 | 0.00 | 0.00 | 0.000 |
| merchant|12 | H14 | 20 | 1.97 | 1.97 | 0.000 |
| merchant|12 | H14+T16 | 20 | 15.54 | 15.54 | 0.000 |
| merchant|12 | H30 | 20 | 15.53 | 15.53 | 0.000 |
| merchant|12 | H30+T30 | 20 | 15.54 | 15.54 | 0.000 |
| merchant|12 | H60 | 20 | 15.54 | 15.54 | 0.000 |

Absolute difference between the unrounded mean and the transcribed value (all are at most 0.0049):

- fixed 4: unrounded diff 0.0049
- fixed 4: unrounded diff 0.0031
- fixed 4: unrounded diff 0.0004
- fixed 4: unrounded diff 0.0032
- fixed 4: unrounded diff 0.0008
- fixed 12: unrounded diff 0.0024
- fixed 12: unrounded diff 0.0005
- fixed 12: unrounded diff 0.0022
- fixed 12: unrounded diff 0.0032
- fixed 12: unrounded diff 0.0006
- merchant 4: unrounded diff 0.0002
- merchant 4: unrounded diff 0.0024
- merchant 4: unrounded diff 0.0030
- merchant 4: unrounded diff 0.0044
- merchant 4: unrounded diff 0.0022
- merchant 12: unrounded diff 0.0000
- merchant 12: unrounded diff 0.0028
- merchant 12: unrounded diff 0.0030
- merchant 12: unrounded diff 0.0016
- merchant 12: unrounded diff 0.0031
- merchant 12: unrounded diff 0.0031

**Decision rule (fixed before the comparison):** MATCH if every absolute difference is ≤ 0.005, otherwise MISMATCH.

**Verdict: MATCH.** All 21 rounded differences are 0.000, and all 21 unrounded differences are ≤ 0.0049, so the
verdict is the same under either reading of the rule.

Note: the task named `src/make_outputs_v10.py` as the reference aggregation. That file does not exist in the
repository, and the existing generator `src/make_outputs.py` does not read `results_horizon.json`. The mean was
computed directly as specified (np.mean of `gain` per setting and arm). No paper, table or macro file was changed.
