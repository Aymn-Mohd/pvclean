# pvclean

## What it does

pvclean simulates dust on PV rows, rain, and a night-time cleaning robot, one year at a time. It compares cleaning policies by the net value they earn under fixed-tariff, merchant, PPA and export-cap contracts. It also holds the code, configs and stored results behind the paper "Contract-Aware Soiling Mitigation for Photovoltaic Plants Under Historical Electricity Market Prices".

## Install

You need Python 3.13. Dependencies are pinned in `pyproject.toml`.

```bash
git clone https://github.com/Aymn-Mohd/pvclean
cd pvclean
uv venv -p 3.13 .venv
uv pip install -p .venv -e ".[test]"
. .venv/bin/activate
```

## Quickstart

This run needs no data and takes a few seconds. It tunes four policies on 2 seeds and tests them on 3 seeds, on a 6-row plant over 60 days.

```bash
python -m pvclean run configs/studies/quickstart.yaml
```

Expected output, with the last line ending in your own path and time:

```text
fixed     fixed      value of cleaning      43.8 USD,   24.0 row cleanings, params {'T': 14}
fixed     threshold  value of cleaning      83.5 USD,   11.0 row cleanings, params {'theta': 0.1}
fixed     econ       value of cleaning      89.5 USD,   11.0 row cleanings, params {'b': 2}
fixed     proposed   value of cleaning      89.1 USD,   15.0 row cleanings, params {'beta': 0, 'kappa': 0.5}
merchant  fixed      value of cleaning       8.5 USD,   12.0 row cleanings, params {'T': 28}
merchant  threshold  value of cleaning      24.0 USD,   11.0 row cleanings, params {'theta': 0.1}
merchant  econ       value of cleaning      45.3 USD,    6.0 row cleanings, params {'b': 2}
merchant  proposed   value of cleaning      24.5 USD,   11.0 row cleanings, params {'beta': 0, 'kappa': 0.5}
wrote .../runs/quickstart/quickstart.json in 0.9 s
```

Value of cleaning is net value minus the net value of no cleaning. Three seeds show that the code runs. They support no conclusion.

## Reproduce the paper results

One command rebuilds every macro, table and figure from the stored results in `results/`. It needs no data:

```bash
python -m pvclean report
```

Each output and the study behind it:

| paper output | stored result | rerun the study |
|---|---|---|
| `table_rq1.tex`, `table_rq1_pes.tex` | `results.json` | `python -m pvclean run configs/studies/generated.yaml` |
| `table_fore.tex` | `results_replay.json` | `python -m pvclean run configs/studies/replay.yaml` |
| `table_exact.tex` | `results_exact.json`, `results_horizon.json`, `results_matched.json` | `python -m pvclean run configs/studies/exact.yaml`, then `horizon.yaml` and `belief_benchmark.yaml` |
| `fig_price.pdf` | `results.json` | `python -m pvclean run configs/studies/generated.yaml` |
| `paper/fig_dryspell.pdf`, `docs/R4_SUMMARY.md` | `r4_rain.json`, `results_r4_*.json`, `results_r3b_rain.json`, `results_matched.json`, `r3_checks.json`, `results_chrono.json` | `python src/make_fig_r4.py`, `python src/make_r4_summary.py` |
| `numbers.tex`, `numbers_v10.tex`, `numbers_pes.tex` | all of the above | `for f in configs/studies/*.yaml; do python -m pvclean run "$f"; done` |

Reruns write to `runs/<study>/`, so they never touch `results/`. Replays need the data cache (see `docs/DATA.md`). `docs/REPRODUCE.md` lists every study and how exactly each one reproduces.

## Concepts

- **Site:** a location with tilt, azimuth, time zone, market and weather source. One YAML file in `pvclean/sites/`.
- **Contract:** what one delivered kWh earns in each hour.
- **Policy:** decides which rows the robot cleans tonight.
- **Forecast:** the value the planner expects, built only from what is known at decision time.
- **Market:** hourly spot prices, generated or real.
- **Study config:** a YAML file in `configs/studies/` that names a runner, its seeds and grids, and its parameters.

## How to add things

Each addition takes one new file and one registry line. `tests/test_extending.py` proves this with toy examples in `tests/examples/`. `docs/EXTENDING.md` has the details.

**A site.** Add `pvclean/sites/toy.yaml`:

```yaml
name: toy
lat: 35.0
lon: 33.0
tilt: 30.0
azimuth: 180.0
tz: Asia/Nicosia
market: generated
weather_source: generated
```

Add `"toy": os.path.join(HERE, "toy.yaml"),` to `REGISTRY` in `pvclean/sites/__init__.py`.

**A contract.** Add `pvclean/contracts/tou.py`, and `"tou": TimeOfUse(),` to `REGISTRY` in `pvclean/contracts/__init__.py`:

```python
class TimeOfUse(Contract):
    name = "tou"

    def hourly_value(self, spot, cfg):
        return np.tile(np.where(np.arange(24) >= 17, 2 * cfg["tariff"], cfg["tariff"]), 365)
```

**A policy.** Add `pvclean/policies/weekly.py`, and `"weekly": Weekly,` to `REGISTRY` in `pvclean/policies/__init__.py`:

```python
class Weekly(Policy):
    name = "weekly"

    def decide(self, s: State) -> Decision:
        if s.d % 7:
            return Decision()
        open_rows = np.where(s.avail)[0]
        return Decision([int(open_rows[np.argmin(s.est[open_rows])])], reason="weekly")
```

**A forecast.** Add `pvclean/forecasts/yesterday.py`, and `"yesterday": Yesterday(),` to `REGISTRY` in `pvclean/forecasts/__init__.py`:

```python
class Yesterday(Forecast):
    name = "yesterday"

    def cutoff(self, d, n_hours):
        return 24 * d

    def predict(self, d, hh, known, vexp, min_hist, roll_days):
        return np.tile(known[(d - 1) * 24:d * 24], len(hh) // 24 + 1)[:len(hh)] if d else vexp[hh].copy()
```

**A price market.** Add `pvclean/markets/flat.py`, and `"flat": FlatMarket(),` to `REGISTRY` in `pvclean/markets/__init__.py`. Then set `market: flat`:

```python
class FlatMarket(Market):
    name = "flat"

    def spot(self, seed, cfg):
        return np.full(8760, 0.05)
```

## Data

AEMO, OMIE and NASA POWER data are downloaded with `pvclean download` and are not redistributed here. `python -m pvclean download <source>` fetches files into a cache outside git and records URL, sha256 and access date. It makes one attempt per URL, and it stops if a source refuses.

| source | used for | terms |
|---|---|---|
| AEMO | 5-minute prices, SA1 and QLD1 | AEMO copyright permissions; check them before reuse |
| OMIE | day-ahead prices, Spain | OMIE terms of use; check them before reuse |
| NASA POWER | hourly weather | NASA POWER terms; cite the source |

`real_prices.npz`, used by the `real`, `roll`, `oracle`, `spain`, `forecast`, `replay` and `forecast_audit` studies, cannot be rebuilt from public sources and is available from the corresponding author on request (contact in CITATION.cff). Some other inputs have no download path. `docs/DATA.md` lists each file.

## Testing

```bash
python -m pytest
```

- `tests/unit/`: one file per module.
- `tests/regression/`: golden files from the code before the restructure, and a byte-for-byte check of paper macros. Golden files are never regenerated to make a test pass.
- `tests/test_smoke.py`: the quickstart through the command line.
- `tests/test_extending.py`: toy additions.
- `tests/test_report_then_suite.py`: `pvclean report`, then the full suite in the same folder.

Without the data cache, tests that need data are skipped.

## Repo layout

```text
pvclean/         the package: core, contracts, policies, forecasts, markets, weather, sites,
                 studies, exact, stats, reporting, cli.py, download.py
configs/studies/ one YAML file per study
tests/           unit, regression, smoke and extension tests
docs/            USAGE, EXTENDING, DATA, REPRODUCE, REVIEW, MIGRATION
docs/records/    pre-registrations, experiment log, phase summaries, decisions
papers/e1_pes/   generated macros and tables
results/         stored results
data/provenance/ download records; the data itself stays outside git
```

## How to cite

Cite the paper and this repository, with the release you used. `CITATION.cff` has the details.

> A. M. M. Rafiq and M. Nassereddine, "Contract-Aware Cleaning Gains Track Dry Spells", submitted to IEEE PES General Meeting 2027.

## Licence

MIT. See `LICENSE`.
