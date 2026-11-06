# Reproducibility

Environment used for the v10 experiment runs (2026-10-11).

| Item | Value |
|---|---|
| CPU model | 13th Gen Intel(R) Core(TM) i7-13700HX |
| Cores | 16 physical cores (8P + 8E), 24 logical CPUs (`os.cpu_count()` = 24) |
| RAM | 31 GB |
| OS | Linux 6.8.0-138-generic (x86_64) |
| Python | 3.13.16 (uv-managed CPython, venv at `.venv/`) |
| SciPy | 1.18.1 (`scipy.optimize.milp`, HiGHS bundled) |
| NumPy | 2.5.4 |
| pandas | 3.0.6 |
| pvlib | 0.16.1 |

## Setup

```bash
uv python install 3.13
uv venv -p 3.13 .venv
uv pip install -p .venv numpy pandas scipy pvlib matplotlib pytest
cd tests && ../.venv/bin/python -m pytest -q    # 27 passed
```

## Parallelism change

`Pool(2)` was replaced with `Pool(os.cpu_count())` in `src/run_experiments.py`, `src/run_new.py`
and every file in `experiments/` that used a pool. `import os` was added to the two `src/`
files that did not already import it. No other code was changed. Other `src/run_*.py` scripts
still use `Pool(2)`.

Results do not depend on the worker count: each run is seeded independently and results are
keyed by run parameters.
