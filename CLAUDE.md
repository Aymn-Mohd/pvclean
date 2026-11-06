# CLAUDE.md (GPU_HOST)

Machine: GPU_HOST, Ubuntu 22.04, RTX 4070 Laptop 8 GB, i7-13700HX, 32 GB. Headless; reached over SSH from the Mac.

Project: E1 (PV cleaning). Role: CPU executor. E1 has no GPU queue. There is no scripts/run_queue.py, configs/queue/ or `<project>-queue` service in this repo.

Layout: package `pvclean/`; one YAML per study in `configs/studies/`; stored results in `results/`; paper in `papers/e1_pes/`; records in `docs/records/`; data outside git in `$PVCLEAN_DATA` or `~/.cache/pvclean/data`. Start with `README.md`, `docs/USAGE.md` and `docs/MIGRATION.md`.

Run a study: `nice -n 10 python -m pvclean run configs/studies/<name>.yaml`. It writes to `runs/<name>/` and never over `results/` unless given `--out results`.

Rules:
- Work without asking questions; log blockers in docs/records/EXPERIMENT_LOG.md or docs/records/decisions.md and continue with what does not depend on them.
- Log every decision, run and deviation in docs/records/EXPERIMENT_LOG.md.
- Pre-register an experiment (log entry, committed alone) before its run starts.
- Apply decision rules verbatim. Anything not pre-registered is labelled ANALYSIS / POST HOC.
- E1 needs no GPU. Do not start GPU jobs. Run long CPU jobs with nice -n 10.
- Never commit data or large binaries. Never rewrite pushed history; never push --force.
- Downloads go through `python -m pvclean download`: one attempt per URL, no workaround on a blocked source.
- Golden files in tests/regression/golden are never regenerated to make a test pass. Fix the code.
- Records in docs/records are kept word for word; append, do not edit.
- Disclose every deviation or fix in docs/records/EXPERIMENT_LOG.md and in the final report.
- Paper numbers come only from `python -m pvclean report`, generated from results/; never typed.
- In repo text, describe the package plainly by what it does. Do not use the words in the BANNED list in tests/test_repo_rules.py.

Branches: main = code; GPU_HOST-runs = results pushed by the GPU_HOST; restructure = the pvclean package. Old heads are tagged `archive/<branch>-20261105`.
