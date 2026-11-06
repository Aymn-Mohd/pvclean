# Contract-aware planner: pseudocode (as implemented)

Source: `src/sim.py`, function `simulate`, policy `"proposed"`. Its ablations are `"proposed_noval"` (contract value replaced by
the constant price p̄) and `"proposed_nobatch"`. Line references are to the R1b tree. Every quantity is per row i, unless it is
marked as site-level.

## Time step, units and geometry

- **Time step.** The simulation is hourly. A year has 8,760 hours, and day d covers hours 24d … 24d+23 in local standard time.
  Every power-to-energy sum is Σ_h P_h · Δt with **Δt = 1 h**. The code sums kW values over hourly indices, so kW·1 h = kWh,
  and no explicit Δt factor appears.
  - Revenue: Σ_h delivered_h [kW] · v_h [USD/kWh].
  - Energy: Σ_h delivered_h.
  - The planner's g and A below use the same convention.
- **Row AC power.** `row_ac(pdc_h, s) = min(P_cap, kWp · pdc_h · s · η)`.
  - kWp = 25 per row, P_cap = 25 / 1.25 = 20 kW, and η = 0.97.
  - pdc_h is the DC output per kWp (kW/kWp).
- **Export cap** (capped contract only): plant delivery is min(Σ_i AC_i, L), with L = 0.75 · 40 · 20 = 600 kW.
- **Dock geometry.** The robot docks at the row-0 end, on the access road side. Row index = distance in row pitches,
  w = 10 m. A mission to row set S takes
  `mission_time(S) = 2 · w · (max S + 1) / u / 60 + t_s · |S|` minutes:
  - drive out to the farthest row and back at u = 0.5 m/s;
  - t_s = 25 min of service per row;
  - budget T_max = `night_min` = 360 min.
  - On the full plant at most 14 rows fit in one night (rows 0–13: 359.3 min).
- **Exposure.** Exposure falls linearly from 1.4 (row 0, nearest the road) to 0.7 (row 39), times a lognormal row factor, and is
  normalised to mean 1. The planner does not know it under station information.

## State kept by the planner

| symbol | code | meaning | initial value |
|---|---|---|---|
| ŝ_i | `est` | estimated soiling ratio (SR) | s_c = 0.995 |
| τ_i | `tau` | days since the last reset (robot cleaning, or rain ≥ 5 mm) | 0 |
| A_i | `A` | estimated lost value accumulated since the last reset, USD | 0 |

- Rows close for crop access: the odd rows on days 60–64, 150–154 and 300–304 (`blackout_mask`).
- `avail = ~black[d]`, the rows open tonight.

## Planner inputs, fixed before the test year (`planner_inputs`)

- clim_h: mean hourly pdc over the training weather seeds 2000–2009.
- vexp_h: the month × hour mean of the training-seed contract values.
- p̄: the production-weighted mean of vexp.
- The price forecast v̂_h comes from `fc_value(cfg.fc_mode, d, hh, val, vexp)`:
  - generated markets: `clim` → vexp_h;
  - R1 replay: F2 rolling 28-day hour-of-day mean of realised values, with `info_cutoff` = 24d.

## Nightly loop, day d = 0 … 364

```
# --- information update (station info: nothing happens here; est was updated at the end of the previous day)

# --- decide tonight's mission (before day d's production)
hh   = hours 24d … min(24d + 24·H_days, 8760) − 1        # H_days = horizon_days = 7; truncated at the year end
                                                        # (with cfg wrap_horizon, hh wraps modulo 8760: R1b continuous runs only)
nd   = |hh| / 24
gain_ih = row_ac(clim_h, s_c) − row_ac(clim_h, ŝ_i)                         # uncapped contracts
gain_ih = min(L, P_h − AC_ih(ŝ) + AC_ih(s_c)) − min(L, P_h),  P_h = Σ_j AC_jh(ŝ)   # capped: the cap is applied to the plant sum
g_i  = (1/nd) Σ_{h∈hh} gain_ih · v̂_h          # expected value per day of having row i clean [USD/day]
Φ_i  = g_i · τ_i − A_i − c_row                 # renewal index: value of resetting now vs. the loss already booked
if row i is open tonight and closed tomorrow:  # anticipate access windows
    L_i = number of closed days of row i in d+1 … d+7
    Φ_i += g_i · L_i
rain_soon = rain forecast flag (≥ 5 mm expected) on day d or d+1     # imperfect: hit 0.8, false alarm 0.05
ready  = {i open tonight : Φ_i ≥ 0}
excess = Σ_{i open tonight} max(Φ_i, 0)
if ready ≠ ∅ and excess ≥ κ · c_mission and not rain_soon:
    cand = {i open tonight : Φ_i ≥ −β · c_row}, sorted by Φ_i descending
    rows = pack(cand)                     # greedy: add row r if mission_time(chosen + [r]) ≤ T_max, else skip r and continue
else:
    rows = ∅

# --- execute (robot works at night, before day-d production)
if rows ≠ ∅:  pay c_mission + c_row·|rows|;  for i in rows: s_i = ŝ_i = s_c, τ_i = 0, A_i = 0

# --- day d production (true state s_i, true pdc_h, realised value v_h)
revenue += Σ_{h in day d} delivered_h · v_h,    delivered_h = Σ_i AC_ih (or min(L, ·) under the cap)

# --- book the estimated loss of day d (after the day: realised pdc and realised v of day d are known)
lost_ih = row_ac(pdc_h, s_c) − row_ac(pdc_h, ŝ_i)        (capped: same cap form as gain_ih, with realised pdc_h)
A_i    += Σ_{h in day d} lost_ih · v_h
τ_i    += 1

# --- end of day: soiling and rain
s_i  = max(s_min, s_i − δ(d) · e_i · ε_i(d))            # truth: site increment x exposure x row noise
ŝ_i  = max(s_min, ŝ_i − δ(d) · (1 + bias))               # station information: the site increment only; bias = 0 by default
rec  = 0.9 if rain_d ≥ 5 mm; 0.2 if 1 ≤ rain_d < 5 mm; else 0
s_i += rec (s_c − s_i);   ŝ_i += rec (s_c − ŝ_i)
if rec ≥ 0.9:  τ_i = 0, A_i = 0 for every row          # full rain is a reset; light rain is not
```

## Recurrences in short

- ŝ_i(d+1) = max(s_min, ŝ_i(d) − δ(d)), then rain recovery ŝ ← ŝ + rec (s_c − ŝ).
- A_i(d+1) = A_i(d) + Σ_{h∈d} [AC(pdc_h, s_c) − AC(pdc_h, ŝ_i(d))] v_h.
- A is reset to 0 by a robot cleaning of row i, or by rain ≥ 5 mm (all rows).
- τ_i(d+1) = τ_i(d) + 1, with the same resets.
- **Cleaning index.** Φ_i = g_i τ_i − A_i − c_row.
  - If the loss rate grows linearly, A(τ) = a τ²/2 and g τ = a τ², so Φ = a τ²/2 − c.
  - The row is cleaned at τ\* = √(2c/a), the classical renewal interval. `tests/test_sanity_tau.py` checks this.

## Dispatch rule and tie-breaking

1. **Gate.** A mission runs only if:
   - at least one open row has Φ ≥ 0;
   - the summed positive Φ over open rows covers κ · c_mission;
   - no full-cleaning rain is forecast for tonight or tomorrow.
2. **Batching.** Once a mission runs, rows down to Φ ≥ −β · c_row are added: rows that are nearly due ride along.
3. **Order.** `np.argsort(−Φ)` with NumPy's default (non-stable) sort.
   - Ties in Φ are broken by that sort's internal order, which is deterministic for a given input.
   - Exact ties occur mainly among rows with identical state, for example rows cleaned together.
4. **Packing.** Greedy in that order. A row that would exceed the night budget is skipped, and later, nearer rows can still be
   added. The result is the feasible set found by `pack`, not an optimal knapsack.
5. **Parameters.** (β, κ) are tuned on the training seeds over β ∈ {0, 0.5, 1}, κ ∈ {0, 0.5, 1, 2}, by training mean net.
   Ties go to the first in grid order.

## Closed rows

- A closed row (access window) is excluded from ready, excess and candidates.
- It keeps soiling, and its τ and A keep growing while it is closed.
- The anticipation term g_i · L_i is added only to rows that are open tonight and closed tomorrow. Such a row can be cleaned
  just before its window: the mission is then worth the L_i days of loss it would otherwise carry.

## Export cap

The capped contract is the fixed tariff with a 600 kW plant export limit. Both the planner's expected gain and its booked loss
use the plant-level cap:

- gain_ih is the change in min(L, P_h) when row i alone is restored to s_c, given all rows at their estimates.
- In hours when the plant is already at the cap, recovered row power is worth 0.
- `proposed_noval` ignores the cap and the contract: it uses the constant price p̄ with uncapped row energy.

## Forecast-matched threshold (FT), for reference

FT uses the same ŝ, clim, price forecast, rain gate, access mask and packing. A row is a candidate when

  NB_i = Σ_{h∈Hb} gain_ih v̂_h − c_row − c_mission / b ≥ 0,

over a horizon of Hb ∈ {7, 14, 30} days, with b ∈ {1, 2, 4, 8} and optional access anticipation. Candidates are sorted by
NB descending and packed. FT keeps no accumulated loss A and no τ.
