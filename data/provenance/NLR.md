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
