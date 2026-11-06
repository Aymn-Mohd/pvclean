# Decisions

Blockers and decisions from the `pvclean` restructure, 2026-11-05.

## Folded from other branches

From `<gpu-host>-runs`: `CLAUDE.md` (rewritten for the new layout), `docs/RESEARCH_PLAYBOOK.md` (now in `docs/records/`), and this log line, kept here so that `EXPERIMENT_LOG.md` stays word for word:

> - 2026-10-16 (ANALYSIS, not pre-registered): horizon file check of `results/results_horizon.json` (sha256 329c702d…783a): 680 records, 0 duplicate keys, all 36 856 solves status 0; recomputed H-arm mean gains vs docs/OPTIMISATION_DIAGNOSTICS.md → MATCH (max |diff| 0.0049). Blockers: `~/RESEARCH_PLAYBOOK.md` missing (copied from <home>/Desktop/icmre-sensing/docs, matches the pasted text); `src/make_outputs_v10.py` missing (means computed directly). See docs/HORIZON_FILE_CHECK.md.

From `e1-overlap-cleanup`, the log note only:

> ## EXP-08 scope decision
>
> EXP-08 moved to a separate paper on 13 Oct 2026. E1 does not report it. The simulator description stays.

That branch's code change is not folded in. It deletes paper macros such as `InspWeekly`, which would break byte-identical output. The paper sources decide this, not the restructure.

## Definition of "the same"

Stored results are not overwritten. New code must match the archived code rerun on this machine, bit for bit. Paper macros must stay byte-identical. Some stored files differ from that rerun: see `docs/REVIEW.md` section 6.

## Blockers

- `real_prices.npz` cannot be rebuilt. See `docs/DATA.md`.
- `new/omie.csv`, `new/nasa_dubai.csv.gz` and the NLR files have no fetch script.

## Wording

Repo text describes the package by what it does, and says nothing about its ambitions. Five single words and one two-word phrase from the restructure brief are not used: they are in that brief, and `tests/test_repo_rules.py` holds the list. Records in this directory are exempt because they are kept word for word.

## Public release brief, 2026-11-06

The brief for the public release was cut off in the middle of Part B step 2, after "the results/*.json the paper macros need,". The rest of the keep list and any later steps did not arrive. Creating the public repository was refused by the session's permission check, so `<user>/pvclean` does not exist yet. The export was staged locally and nothing was published.

Update, 2026-11-06: `<user>/pvclean` was created, public and empty, after the owner allowed it. Nothing has been pushed to it. The rest of the brief is still missing.
