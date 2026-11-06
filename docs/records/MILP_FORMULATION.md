# MILP formulation of the exact benchmark (as implemented)

Sources: `src/exact.py` (clairvoyant optimum J\*, `row_tables`, `solve`, `schedule_value`), `src/optimisation.py`
(receding-horizon MILP, `make_mpc`), drivers `src/run_exact.py` and `experiments/horizon_sensitivity.py`. Numbers in section 6
come from the stored `results/results_exact.json`, `results/results_horizon.json` and `results/results_matched.json` through
`experiments/milp_gaps.py`, which writes `results/milp_gaps.json`. Nothing was re-solved for this document.

## 1. Instance

- 6 rows (`n_rows=6`), night budget `night_min = 100` min, decision window days `d0 = 120` to `d1 = 180`, so D = 60 days.
- Seeds 0–19 (20 instances per setting). Settings: contract fixed or merchant, with c_row = 4 or 12 USD.
- All other parameters are the defaults in `sim.CONFIG`: c_mission = 10 USD, s_clean = 1 − 0.005 = 0.995, s_min = 0.5, rain
  recovery 0.9 (≥ 5 mm) and 0.2 (1–5 mm), and the crop-access windows (odd rows closed on days 150–154 inside the window).
- **Mission time.** For a row set S, `mission_time(S) = 2·w·(max S + 1)/u/60 + t_s·|S|` minutes, with w = 10 m, u = 0.5 m/s
  and t_s = 25 min. The dock is at the row-0 end, and the robot drives out to the farthest row in S and back.
- With 100 min, every feasible set has |S| ≤ 3. There are 41 feasible non-empty subsets of the 6 rows.

## 2. Clairvoyant optimum J\* (`exact.solve`)

### Sets

- Rows: i ∈ I = {0, …, n−1}.
- Reset nodes: c ∈ {0, …, D−1}, where node 0 is the free start at d0 with every row at s_clean. There is also an end node D.
- Mission nights: t ∈ {1, …, D−1}. No mission is possible at t = 0, because the rows start clean.
- Feasible missions: 𝒮 = {S ⊆ I, S ≠ ∅ : mission_time(S) ≤ T_max}, with T_max = `night_min`.

### Parameters: revenue table `row_tables`

Rev[i, c, d] is the revenue of row i on day d (d ≥ c) when its last reset was at window day c. It is built by forward simulation
from s_i = s_clean at day c, using the **true** hourly DC output, row exposure e_i, row noise ε_i(d), site increment δ(d), rain
and contract value v_h of that seed:

```
Rev[i,c,d] = Σ_{h in day d} min(P_cap, kWp · pdc_h · s_i(d) · η) · v_h        (Δt = 1 h, so kW·h = kWh)
s_i(d+1)   = max(s_min, s_i(d) − δ(d) e_i ε_i(d));   then, if rain_d ≥ 1 mm:  s_i ← s_i + rec_d (s_clean − s_i)
```

- P_cap = kWp / (DC:AC ratio), and η = 0.97.
- The soiling update happens after day d's revenue, in the same order as `sim.simulate`.
- Rain recovery is part of the trajectory, not a reset node. A row's output therefore depends only on its last robot reset,
  which is what makes the path formulation exact.

### Variables (all binary)

- z[i, c, c′] for 0 ≤ c < c′ ≤ D: the consecutive resets of row i are at c and c′ (c′ = D means no further reset).
- y[S, t] for S ∈ 𝒮 and t ∈ {1, …, D−1}: mission S runs on the night before day d0 + t.

### Objective

The code minimises the negative of:

```
max  Σ_i Σ_{c<c′} z[i,c,c′] · Σ_{d=c}^{c′−1} Rev[i,c,d]  −  Σ_t Σ_S y[S,t] · (c_mission + c_row·|S|)
```

### Constraints

1. Each row leaves the start node once: Σ_{c′>0} z[i,0,c′] = 1 for every i.
2. Flow conservation at every reset node t = 1, …, D−1: Σ_{c0<t} z[i,c0,t] = Σ_{c′>t} z[i,t,c′]. The end node then receives
   exactly 1.
3. Linking, so that a row is reset at t exactly when a mission containing it runs at t:
   Σ_{c0<t} z[i,c0,t] = Σ_{S∋i} y[S,t] for every i and t.
4. At most one mission per night: Σ_S y[S,t] ≤ 1 for every t.
5. Access: y[S,t] has upper bound 0 when any row of S is closed on day d0 + t.

### Linearisation

Soiling makes revenue a nonlinear, history-dependent function of the cleaning decisions. Two devices make the model linear:

- **Revenue.** Precomputing Rev for every (last reset, day) pair makes revenue linear in the arc variables z, the
  "reset-arc" or shortest-path formulation: arc (c, c′) carries the summed revenue of days c to c′−1.
- **Mission costs.** The fixed mission cost and the night time budget become linear because the feasible row sets are
  enumerated and selected through y. The time budget is enforced by construction of 𝒮.

No big-M constraints are used.

### Scoring and truncation at day 60

- `schedule_value` re-evaluates the schedule on the same Rev table.
- J\* is reported as the gain over no cleaning (`schedule_value(Rev, [])`).
- **The value stops at d1, day 60 of the window.** There is no terminal value, and soiling left at the end of the window is not
  charged. Every arm and policy is scored over the same 60 days.

## 3. Receding-horizon MILP (`optimisation.make_mpc`)

It is solved every night d inside `sim.simulate(policy="mpc")`, and only the first night's mission is executed.

### Nights without a solve

If rain ≥ 5 mm is forecast in the next `rain_fc_days = 2` days (the same imperfect forecast as the planner's), no MILP is solved
and nothing is cleaned.

### Horizons

- Decision horizon H = min(horizon, d1 − d).
- Valuation horizon HH = min(H + tail, d1 − d) when tail > 0, else HH = H.

### Belief (matched arms)

- Expected site increment `exact.expected_increment`: seasonal mean plus expected dust-event loss.
- No rain recovery.
- Equal row exposure (e = 1).
- Production: the training climatology `clim`.
- Prices: `forecasting.value_forecast(price_mode, d, …)`, which is `vexp` under `clim`.
- Start state: the planner's estimate `est`.
- Oracle flags (`oracle_expo`, `oracle_inc`, `oracle_pdc`, `price_mode='perfect'`, `info='perfect'`) replace one item each, for
  the information ladder L1–L7 only.

### Nodes and arcs per row

| arc | meaning | value |
|---|---|---|
| S → E | no reset in the window | R0 over all HH days |
| S → t | first reset at t | R0 over days < t |
| t → t′ | reset at t, next reset at t′ | Rr over days t … t′−1 |
| t → E | reset at t, no further reset | Rr over days t … HH−1, **tail included** |

- R0 = revenue from the current estimate.
- Rr = revenue after a reset. It is the same for all rows unless `oracle_expo` is set.
- t ranges over 0 … H−1, and y[S, t] exists only for t < H.
- y[S, 0] is also fixed to 0 if any row in S is unavailable tonight.

The constraints are the same as section 2: one unit of flow out of S, conservation at each t, linking to y, at most one mission
per night, and access.

### Terminal tail

- The tail consists of days H … HH−1. They are valued with rows evolving under expected soiling and no further cleaning, so a
  cleaning near the end of the decision horizon is credited with the revenue it keeps producing in the tail.
- The tail is **truncated at the end of the instance (day 60)**: HH ≤ d1 − d. Near the end of the window the effective horizon
  and tail therefore shrink. For example, at d = d0 + 40, H30+T30 has H = HH = 20.
- H60 from d0 covers the whole window.

### Model size per solve

n(1 + 2H + H(H−1)/2) + H·|𝒮| binary variables. For H = 30 that is 6 · 496 + 30 · 41 = 4,206.

## 4. Solver

- `scipy.optimize.milp` (SciPy 1.18.1, bundled HiGHS 1.12.0), with integrality on every variable and bounds [0, ub].
- **Clairvoyant J\*:** `time_limit = 120` s, `mip_rel_gap = 1e-4`.
- **Horizon study** (`horizon_sensitivity.py`): `time_limit = 60` s, `gap = 1e-3`.
- `make_mpc`'s own default is 20 s with gap 1e-3; this is the v9 path.
- A solve is called optimal only if `status == 0` and the reported MIP gap is below the requested tolerance.

## 5. Percentages in `paper/table_exact.tex`

They are **ratios of means**: 100 · mean_s J(s) / mean_s J\*(s) over the 20 instances (`make_outputs_v10.py`, `pct[kk]`).
Section 6 also gives the mean of per-instance ratios for comparison.

- Mean of ratios is undefined when J\* = 0; no instance here has J\* ≤ 1 USD.
- It differs strongly from the ratio of means for merchant at 12 USD/row, where J\* is small (mean 21.6 USD) and several
  policies have negative J on some instances.

## 6. Results from stored runs (ANALYSIS)

The paired gap J\* − J is in USD per 60-day instance: mean and 95% paired t-interval over the 20 seeds.

- RoM = ratio of means (the table's percentage).
- MoR = mean of per-instance ratios.
- Policies use station information (results_exact.json "site"); FT comes from results_matched.json part_b.

| setting | J\* mean | arm | J\* − J mean [95% CI] | RoM % | MoR % |
|---|---|---|---|---|---|
| fixed, 4 | 154.2 | MILP H14 | 12.4 [8.9, 15.9] | 92.0 | 92.3 |
| | | MILP H30+T30 | 6.8 [3.3, 10.3] | 95.6 | 95.6 |
| | | fixed | 7.2 [3.7, 10.7] | 95.3 | 95.3 |
| | | threshold | 15.7 [10.0, 21.4] | 89.8 | 88.2 |
| | | econ | 13.6 [9.6, 17.5] | 91.2 | 89.9 |
| | | FT | 7.3 [4.6, 10.1] | 95.2 | 95.1 |
| | | planner | 13.7 [10.5, 17.0] | 91.1 | 89.9 |
| fixed, 12 | 87.0 | MILP H14 | 11.3 [8.0, 14.6] | 87.0 | 84.0 |
| | | MILP H30+T30 | 5.6 [2.0, 9.3] | 93.5 | 94.2 |
| | | fixed | 36.0 [30.4, 41.5] | 58.6 | 50.5 |
| | | threshold | 22.8 [14.3, 31.2] | 73.8 | 67.9 |
| | | econ | 16.2 [11.7, 20.7] | 81.4 | 79.8 |
| | | FT | 7.9 [4.5, 11.3] | 90.9 | 89.5 |
| | | planner | 19.3 [8.0, 30.6] | 77.8 | 79.7 |
| merchant, 4 | 65.3 | MILP H14 | 3.3 [1.8, 4.8] | 94.9 | 95.3 |
| | | MILP H30+T30 | 2.4 [1.0, 3.8] | 96.4 | 96.5 |
| | | fixed | 21.6 [18.8, 24.4] | 66.9 | 63.8 |
| | | threshold | 12.4 [7.1, 17.7] | 81.0 | 78.0 |
| | | econ | 12.9 [8.9, 17.0] | 80.2 | 78.4 |
| | | FT | 5.1 [2.8, 7.4] | 92.2 | 91.0 |
| | | planner | 23.3 [18.9, 27.7] | 64.3 | 59.9 |
| merchant, 12 | 21.6 | MILP H14 | 19.6 [13.8, 25.4] | 9.1 | 4.9 |
| | | MILP H30+T30 | 6.0 [4.0, 8.1] | 72.0 | 54.9 |
| | | MILP H60 | 6.0 [4.0, 8.1] | 72.0 | 54.9 |
| | | fixed | 15.9 [13.6, 18.1] | 26.6 | −16.8 |
| | | threshold | 19.1 [11.9, 26.3] | 11.5 | −70.7 |
| | | econ | 13.9 [10.4, 17.4] | 35.4 | −18.2 |
| | | FT | 17.9 [13.2, 22.6] | 17.1 | 8.5 |
| | | planner | 17.1 [9.1, 25.1] | 20.9 | −7.1 |

`results/milp_gaps.json` holds every arm, including H07, H30, H14+T16 and the L1–L7 ladder.

### Solve times and failures

- **Clairvoyant J\*:** all 80 solves have status 0. The largest MIP gap is 9.9e-5. Solve time is not stored in
  `results_exact.json`.
- **Receding-horizon arms:** in every setting and arm, 20 runs and 1,084 solves. Every solve has status 0, with no solve
  lacking a solution and 0 schedule-constraint violations.
  - Largest MIP gap: 0 in the H arms; up to 1.0e-3 in the L1, L6 and L7 ladder arms (tolerance 1e-3).
  - Longest single solve: 1.7 s for H30+T30 and 18.7 s for H60 at merchant/12, against a 60 s limit. No solve reached the
    time limit.
  - Mean wall time per 60-day run: H14 about 9 s, H30+T30 about 45 s, H60 at merchant/12 173 s.

### Notes

- `results_matched.json` holds only `part_b`. The deterministic belief-world Part A table cited in
  `docs/OPTIMISATION_DIAGNOSTICS.md` is not in the stored file. It is not used here.
- J\* is clairvoyant on the true instance. The MILP arms are optimal only for their own belief model and are scored in the
  stochastic simulator, so J\* − J ≥ 0 is expected but not guaranteed per instance. Every per-setting mean gap above is positive.
