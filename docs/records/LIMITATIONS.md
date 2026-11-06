# Limitations (v10)

1. **Soiling is generated.** No measured soiling series drives any main result. NREL/NLR site statistics are used only as a sensitivity range.
2. **Cost, service-time and cleaning-effectiveness values are assumptions** (4 USD/row, 10 USD/mission, 25 min/row, residual 0.5 %).
3. **Three price years per market.** Confidence intervals in the real-market tables are conditional on the observed years and on the generator; they are not evidence of generalisation across markets or years.
4. **Forecast scenarios F0 and the tuning step are not causal for the early folds** (leave-one-year-out uses later years). F1 (previous year), F2 (rolling) and F3 (next 24 h) are causal; F3 is a published day-ahead product in Spain only. F4 is an oracle.
5. **Price/clock alignment.** Market-time hour indices (AEST, CET/CEST) are used as the plant's clock hour; no solar-time alignment is applied.
6. **Exact benchmarks are small** (6 rows, 60 days, at most 3 rows per mission, 20 instances per setting). They do not certify anything for the 40-row annual problem.
7. **The receding-horizon MILP is a benchmark under its own model**, not an upper bound for deployable policies: it assumes expected dust, no rain and equal row exposure. Its performance depends on horizon and terminal valuation (see OPTIMISATION_DIAGNOSTICS.md).
8. **Solver**: `scipy.optimize.milp` (HiGHS bundled with SciPy 1.18.1), single instance per call, relative-gap tolerance 1e-3 (receding horizon) / 1e-4 (clairvoyant), 20–60 s limits; a result is called optimal only when the solver status is 0 and the reported gap is within tolerance.
9. **No hardware validation.** Everything is simulated; rover data are not yet used.
10. **Exchange rates** (0.65 USD/AUD, 1.08 USD/EUR) are fixed constants; AEMO spikes up to ≈ 9–10 USD/kWh are kept and dominate the variance of merchant revenue in SA1/QLD1.
