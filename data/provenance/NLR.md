# NREL / NLR soiling statistics: provenance

Source: the NREL (now NLR) PV soiling map site table and monthly soiling rates, cited in the paper as `nlrsoiling`, https://www.nlr.gov/pv/soiling. The local copies and their sha256 hashes:

- `data/new/nlr_monthly.csv` sha256 `a4ae1bd5aa8ae13a07d5a82697c6bbf0338e07c0786965ca7d2f805e13f15f8d`
- `data/new/nlr_sites.csv` sha256 `ae0961d2c0d106fd507b1bca843d10406c10f276241bc9fd418694ecb0b5e321`

Reproduced by `src/provenance_r1b.py` (the same rule as `src/make_outputs.py`, lines 422-428). Run from `src/`.

## Rule

- `nlr_monthly.csv` stores `soiling_rate_per_day` as a negative fraction per day. The loss rate in %/day is r = -100 x soiling_rate_per_day.
- Rows with a missing rate are dropped: 27 of 1752, leaving 1725 site-months.
- **NrelSites** = number of sites with at least one monthly rate.
- **NrelMedian** = median over all site-months. It is not a median over sites.
- **NrelSiteMax** = largest per-site mean of monthly rates, with every month weighted equally regardless of `interval_count`.

## Result

| statistic | value | paper macro |
|---|---|---|
| sites in the site table | 255 | |
| sites without monthly rates ("No monthly rates provided for low-soiling sites") | 109 | |
| sites with monthly rates | **146** | NrelSites = 146 |
| median site-month loss rate | **0.1000 %/day** | NrelMedian = 0.10 |
| quartiles of site-month rates | 0.080, 0.140 %/day | |
| median of site means | 0.1075 %/day | NrelSiteMedian = 0.11 |
| 90th percentile of site means | 0.1858 %/day | NrelSitePn = 0.19 |
| largest site mean | **0.2958 %/day** (`13040_ac_power_inv_23331`) | NrelSiteMax = 0.30 |

All three cited values reproduce: 146 sites, 0.10 %/day and 0.30 %/day.

## Caveats

- **The 146 sites exclude the 109 low-soiling sites** of the 255-site table: insolation-weighted soiling ratio above 0.99, for which the map gives no monthly rates.
  - The "median US soiling rate" of 0.10 %/day is therefore the median of the sites that soil measurably.
  - Over all 255 sites the median would be lower.
- "Median" in the paper is the median of site-months, not of sites. The median of site means is 0.11 %/day.
- The sensitivity runs (`results_nrel.json`) use soil_mean = 0.0011 for "med" and 0.0019 for "p90", per day as a fraction (0.11 and 0.19 %/day), with season_amp = 0.16. That is, they use the median and 90th percentile of **site means**, not the 0.10 %/day site-month median quoted next to them.
- {'PV System': 244, 'Soiling Station': 11}; 15 US states. No Gulf site is included.

## Download date and hashes (added in release 1.4.1)

- Download date: not recorded. The earliest record is the files' first commit to the private development repository, on 2026-10-11 (commit 3d4e18c), with the sha256 hashes above. The copies in the data cache had the same hashes on 2026-11-08.
- `data/new/nlr_monthly.csv`: 92,427 bytes, sha256 `a4ae1bd5aa8ae13a07d5a82697c6bbf0338e07c0786965ca7d2f805e13f15f8d`.
- `data/new/nlr_sites.csv`: 30,975 bytes, sha256 `ae0961d2c0d106fd507b1bca843d10406c10f276241bc9fd418694ecb0b5e321`.
- No script in this repository fetches these files. Download the site table and the monthly soiling rates from https://www.nlr.gov/pv/soiling, save them under the names above, and compare the sha256 hashes.

## Download instructions for the other sources

`python -m pvclean download <source>` fetches each file once into the data cache, `$PVCLEAN_DATA` or `~/.cache/pvclean/data`. It records URL, sha256 and access date in `provenance/<source>.json` in the cache, and stops at the first refused request. The URLs come from `pvclean/download.py` and `data/provenance/r1_downloads.json`.

**AEMO** (`python -m pvclean download aemo`)
- What: 5-minute regional prices (RRP, AUD/MWh) for SA1 and QLD1, June 2022 to December 2025.
- Files: one per month and region, `https://www.aemo.com.au/aemo/data/nem/priceanddemand/PRICE_AND_DEMAND_<YYYYMM>_<REGION>.csv`, saved as `raw/aemo/PRICE_AND_DEMAND_<YYYYMM>_<REGION>.csv`.
- `SETTLEMENTDATE` is the interval end, in market time (UTC+10, no daylight saving).

**OMIE** (`python -m pvclean download omie`)
- What: day-ahead marginal prices, the `marginalpdbc` files.
- Yearly archives: `https://www.omie.es/es/file-download?parents%5B0%5D=marginalpdbc&filename=marginalpdbc_<YYYY>.zip`. Each holds one file per day, `marginalpdbc_<YYYYMMDD>.1`.
- File format: semicolon-separated lines `year;month;day;period;price_PT;price_ES;`, in EUR/MWh. Periods are hours on the Spanish clock (23 or 25 on daylight-saving days), and quarter-hours from 1 October 2025.
- The command fetches the 2022 archive, of which December 2022 is used as warm-up (`raw/omie/2022/`).
- The 2023 to 2025 prices are read from `new/omie.csv`: sha256 `b480d9cff4c1cd5b7a4e4b56626ef3e736792b10373f97e5062fa1c7a5ee802d`, recorded in `r1_downloads.json`. Its columns are `date, period, price_PT_eur_mwh, price_ES_eur_mwh, source_file, resolution_min`, one row per period of each `marginalpdbc_<YYYYMMDD>.1` file of the 2023, 2024 and 2025 archives. No script in this repository builds it. To rebuild it, download those three archives and write one row per line of each daily file, with `source_file` the daily file's name. `resolution_min` as recorded is 60 up to 30 September 2025 and 15 from 1 October 2025, except 14 on 26 October 2025 (100 quarter-hour periods). Then compare the sha256.

**NASA POWER** (`python -m pvclean download nasa-power`, optionally `--sites <names>`)
- What: the hourly point API, community RE, time standard UTC, one CSV per site and calendar year, 2001 to 2025.
- Request: `https://power.larc.nasa.gov/api/temporal/hourly/point?parameters=ALLSKY_SFC_SW_DWN,ALLSKY_SFC_SW_DNI,ALLSKY_SFC_SW_DIFF,CLRSKY_SFC_SW_DWN,T2M,WS10M,PRECTOTCORR&community=RE&longitude=<lon>&latitude=<lat>&start=<YYYY>0101&end=<YYYY>1231&format=CSV&time-standard=UTC`.
- Saved as: `raw/nasa_power/<site>_<YYYY>.csv`. Site coordinates are in `pvclean/download.py`; expected hashes are in `data/provenance/r3_nasa_power.json`, `r4_nasa_power.json` and `r5_nasa_power.json`.
- Stamps are UTC hour starts. `pvclean.weather.build.sites()` writes `site_wx.npz` on the UTC clock, and `pvclean.weather.nasa_site.to_time_base` moves each series to the price clock of its site (`time_base` in `pvclean/sites/<site>.yaml`): `Etc/GMT-10` (UTC+10) for the SA1 and QLD1 sites, and `Europe/Madrid` for the Spanish sites, with 23- and 25-hour days resampled to 24 positions as the OMIE prices are.

Then build the price and weather files with `python -c "from pvclean.markets.build import build; build()"` (writes `real_prices_v2.npz`) and `python -c "from pvclean.weather.build import sites; sites()"` (writes `site_wx.npz`).
