# Data

Market and weather data stay outside git. The cache is `$PVCLEAN_DATA`, or `~/.cache/pvclean/data`. Only download records in `data/provenance/` are tracked.

## Downloads

```bash
python -m pvclean download nasa-power   # 75 files: 3 sites, 2001 to 2025
python -m pvclean download aemo         # monthly price files, SA1 and QLD1
python -m pvclean download omie         # December 2022 files, warm-up only
```

- Each URL gets one attempt. There are no retries and no changed headers.
- A failed request stops that source, because a block applies to the whole source.
- The record goes to `<cache>/provenance/<source>.json`, with URL, status, size, sha256, expected sha256 and access date.
- On 2026-11-05 one file from each of the three sources was fetched this way, and each hash matched the stored record.

## Files the code reads

| cache path | built from | can it be rebuilt? |
|---|---|---|
| `raw/aemo/`, `raw/nasa_power/`, `raw/omie/` | `pvclean download` | yes, except the OMIE file below |
| `new/omie.csv` | OMIE day-ahead 2023 to 2025 | no script in this repository fetches it; the record is in `data/provenance/r1_downloads.json` |
| `new/nasa_dubai.csv.gz` | NASA POWER, Dubai | no script in this repository fetches it |
| `new/nlr_monthly.csv`, `new/nlr_sites.csv` | NREL/NLR soiling map | no script; see `data/provenance/NLR.md` |
| `real_prices_v2.npz` | `pvclean.markets.build.build()` | yes, from the raw files and `new/omie.csv` |
| `site_wx.npz` | `pvclean.weather.build.sites()` | yes, from `raw/nasa_power/` |
| `dubai_wx.npz` | `pvclean.weather.build.dubai()` | yes, from `new/nasa_dubai.csv.gz` |
| `real_prices.npz` | older pipeline | **no**: its input `data/aemo_merged/` no longer exists |

`real_prices.npz` feeds `real`, `roll`, `oracle`, `spain`, `forecast`, `replay` and `forecast_audit`. It cannot be rebuilt from public sources and is available from the corresponding author on request (contact in CITATION.cff). Its sha256 is `5e27fc53bf5e44cc5e124ac0bee22e3f47c8e519a4ec350bb2e94dc049630a67`.

## What a fresh clone can do

Without data: install, unit tests, the generated and exact regression cases, the quickstart, and `pvclean report`. Macros use `results/macro_inputs.json` for the numbers that came from data. With data: everything.

## Blocked sources

BoM Climate Data Online and AEMET OpenData are not download sources. BoM refused automated access and AEMET needs an API key. See "R3b blockers" in `docs/records/EXPERIMENT_LOG.md`.

## Terms of use

Check the terms of AEMO, OMIE, NASA POWER and NREL before you reuse their data. This repository contains no market or weather data files, and its history starts at the public release.
