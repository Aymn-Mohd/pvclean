# Extending pvclean

Each addition takes one new file and one line in that package's `REGISTRY`, in its `__init__.py`. Core code stays unchanged. `tests/test_extending.py` runs a toy version of each, using `register()` in place of the registry line. The examples are in `tests/examples/`.

## Policy

Subclass `pvclean.policies.Policy` and implement `decide(self, s) -> Decision`.

- `s` is a `State`: day `s.d`, open rows `s.avail`, estimates `s.est`, days since cleaning `s.tau`, estimated lost value `s.A`, and forecasts through `s.forecast(hh)`.
- `Decision(rows, wanted, reason)` holds tonight's rows. Call `pvclean.core.robot.pack` to respect the night budget and battery.
- Override `book(self, s, hs)` if the policy keeps a running account after each day.
- Set `inspects = False` if mobile patrols should not apply.
- Add a grid under `grids:` in the study config to tune it.

## Contract

Subclass `pvclean.contracts.base.Contract` and implement `hourly_value(self, spot, cfg)`. Set `capped = True` to apply the export limit. For interval-level values, set `interval_key` and implement `from_interval(self, a, cfg)`.

## Forecast

Subclass `pvclean.forecasts.base.Forecast`. `cutoff(d, n_hours)` states the first hour the provider may not see. The caller passes only `val[:cutoff]`, so a later value cannot be read. Set `deployable = False` for an oracle. Select it with `fc_mode`.

## Market

Subclass `pvclean.markets.base.Market` and implement `spot(self, seed, cfg)`, returning 8760 hourly prices in USD/kWh. Select it with `market`.

## Site

Add a YAML file with `name`, `lat`, `lon`, `tilt`, `azimuth`, `tz`, `market` and `weather_source`, and a line in `pvclean/sites/__init__.py`. A site with `weather_source: nasa_site` also needs `time_base`, the clock of its prices, and its table in `site_wx.npz`.

## Weather source

Add a function `(seed, cfg) -> dict(pdc, rain, clear_pdc)` and a line in `pvclean/weather/__init__.py`. Select it with `weather_source`.

## Study runner

Add a function taking a `Study` and returning JSON-ready data, and a line in `RUNNERS` in `pvclean/studies/__init__.py`.

## Changing what is true in a year

Pass a `pvclean.core.world.World` to `simulate` to replace weather, dust, exposure, value or the rain forecast for one run. `pvclean.exact.belief_world` is an example.
