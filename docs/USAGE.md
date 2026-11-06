# Usage

## Commands

```bash
python -m pvclean run <config.yaml> [--out DIR] [--workers N]
python -m pvclean tune <config.yaml> [--contract merchant] [--policies fixed proposed]
python -m pvclean report [--out DIR] [--results-out DIR] [--no-figures] [--refresh-inputs] [--summaries]
python -m pvclean download <nasa-power|aemo|omie> [--limit N]
```

`run` writes to `runs/<study>/`. Pass `--out results` only if you mean to replace a stored result. `report` reads `results/` and writes to `papers/e1_pes/`. `--refresh-inputs` recomputes `results/macro_inputs.json` from the data cache. `--summaries` rewrites the phase summaries in `docs/records/`.

## A study config

```yaml
study: my_study
runner: quickstart            # a name in pvclean.studies.RUNNERS
output: my_study.json
protocol:                     # overrides pvclean/protocol.yaml
  train_seeds: [1000, 1001]
  test_seeds: {start: 0, stop: 10}
  grids:
    proposed: {beta: [0, 0.5], kappa: [0.5, 2]}
params:                       # read by the runner
  site: dubai
  contracts: [merchant]
  policies: [fixed, proposed]
  over: {c_row: 8.0}          # any key of pvclean/defaults.yaml
```

## From Python

```python
from pvclean import model

cfg = model.merged({"c_row": 8.0})
clim, vexp, pbar = model.planner_inputs("merchant", cfg)
out = model.simulate("proposed", {"beta": 0.5, "kappa": 0.5}, "merchant", 0, cfg=cfg, clim=clim, vexp=vexp, pbar=pbar)
print(out["net"], out["n_clean"], out["sched"][:3])
```

To run tuning and evaluation, use `pvclean.studies.runner.Runner` with a `Protocol`. Results do not depend on worker count, because every job is seeded and `pool.map` keeps job order.

## Parameters

Every model value is in `pvclean/defaults.yaml`. Seeds and grids are in `pvclean/protocol.yaml`. The defaults are the values of the original code.
