# The oracle's night-budget repair and its upper bound

This note describes `pvclean/exact/oracle.py` and nothing else. Line numbers refer to that file in release 1.4.1.

## The problem the oracle solves

The oracle plans one plant-year of `n` rows over `D` window nights with perfect information. Prices, rain, dust and per-row soiling are known, unless an R7 variant replaces one of them. The robot, night budget, access windows and costs are the simulator's.

- Row `i` is reset (cleaned) on a set of nights. Its revenue depends only on its own reset nights. `G[i, c, e]` is the revenue of row `i` over window days `c` to `e - 1` when its last reset was night `c` (`path_values`, lines 43-59). Night 0 is the clean start, not a decision.
- A reset of row `i` on night `t` costs `c_row`. It is impossible (cost infinity) when the row is closed that night by an access window (`base_cost`, lines 115-120).
- Rows interact in two ways only:
  - A night with at least one reset is a mission and costs `c_mission` once.
  - The rows cleaned on one night must fit the night budget: `mission_time(rows) <= night_min`. Here `mission_time` is travel to the farthest row and back plus `service_min` per row (`pvclean/core/robot.py`, `mission_time`).

The value of a schedule is the sum of the rows' revenues, minus `c_row` per reset, minus `c_mission` per non-empty night.

## Feasible schedules: `evaluate` and the night-budget repair (lines 91-112)

`evaluate(G, base, nights, cfg)` gets a set of candidate mission nights and returns a feasible schedule with its value.

1. **Solve each row alone.** For each row, `row_dp` (lines 62-77) finds the best set of reset nights among the candidates, at the current reset prices. The row problems are independent, so this step is exact.
2. **Check every night against the budget.** Group the chosen resets by night. If every night fits, return the sum of the row values minus `c_mission` per non-empty night (line 102). Empty nights are not charged.
3. **Repair each over-full night `t`.**
   - For every row, compute its loss: its current value minus its value when it may not be reset on night `t` (lines 105-106).
   - Sort the rows booked on `t` by loss, smallest first (line 107).
   - Remove rows in that order until the remaining rows fit the budget.
   - Each removed row is barred from that night: its reset price on `t` is set to infinity (line 112). The bar stays for the rest of this call. A removed row may still be reset on any other candidate night.
4. Go back to step 1 with the new prices.

**Why the loop ends.** A row is removed from a night only while it is booked there, so its price on that night was finite. Every pass through step 3 therefore turns at least one finite price into infinity. There are at most `n x D` such prices, so the loop ends.

**Why a removal step always reaches the budget.** Removing a row never increases `mission_time`: the farthest row cannot move farther away, and service time falls. The empty set takes 0 minutes.

**Why the result is feasible.**
- The loop returns only when every night fits the budget.
- Closed rows keep infinite prices from `base_cost`, so they are never booked.
- Every non-empty night is charged `c_mission` once.

The repair is greedy. A schedule from `evaluate`, and so from `local_search` (lines 123-150) and `solve_oracle` (lines 194-208), is feasible but not necessarily optimal. Its value is a lower bound on the optimum.

## The upper bound: `cap_rows` and `upper_bound` (lines 153-191)

### Step 1: replace the night budget by a row count `K`

`cap_rows` (lines 153-158) returns the largest `K` such that the `K` nearest rows `{0, ..., K-1}` fit in one night.

For any set `S` of distinct rows, the farthest row index plus one is at least `|S|`. So travel to the farthest row is at least travel for the nearest `|S|` rows, and service time is the same. Hence `mission_time(S) >= mission_time({0, ..., |S|-1})`.

So if `S` fits the budget, the nearest `|S|` rows fit too, and `|S| <= K`. Every schedule that satisfies the night budget therefore also satisfies

    sum over rows i of x[i, t] <= K * y[t]      for every night t,

where `x[i, t] = 1` if row `i` is reset on night `t`, and `y[t] = 1` if night `t` is a mission. Replacing the budget by this count can only enlarge the set of allowed schedules, so the best value under it is at least the true optimum.

### Step 2: price the coupling constraints (Lagrangian relaxation)

Two constraints couple the rows:
- the link `x[i, t] <= y[t]` (a row is cleaned only on a mission night);
- the row count `sum_i x[i, t] <= K y[t]`.

Give the link the multiplier `lam[i, t] >= 0` and the row count the multiplier `mu[t] >= 0`. Then add the penalty terms

    sum over i, t of lam[i, t] * (y[t] - x[i, t])   +   sum over t of mu[t] * (K y[t] - sum_i x[i, t])

to the objective, and drop the two constraints.

For any schedule that meets them, both penalty terms are non-negative. So for any non-negative multipliers, the maximum of the penalised objective over all `x` and `y` is at least the value of every allowed schedule. It is therefore an upper bound on the optimum of the true problem.

### Step 3: compute that maximum exactly (lines 168-175)

Once the coupling constraints are priced, the problem splits into independent pieces.

**Rows.** Each row maximises its revenue minus `c_row + lam[i, t] + mu[t]` per reset (line 168). `row_dp` solves this exactly over all nights `1 .. D-1`, with closed rows at infinite price. Summed over rows, this is `vals.sum()`.

**Nights.** Each night chooses `y[t]` to maximise `y[t] * (sum_i lam[i, t] + K mu[t] - c_mission)`. The optimum is `max(gain[t], 0)` (lines 173-175).
- The sum runs over open rows only. A closed row has `x[i, t] = 0` in every allowed schedule, so its link constraint is never binding; leaving it out is the same as setting `lam[i, t] = 0` for it.
- Night 0 is the clean start and has no gain.

`L = vals.sum() + sum_t max(gain[t], 0)` (line 175) is therefore the exact maximum for the current multipliers, and a valid upper bound.

### Step 4: keep the smallest bound found

The multipliers are improved by projected subgradient steps (lines 184-190) and stay non-negative through `np.maximum(0, ...)`. The step size affects only how tight the bound becomes, not whether it is valid.

The smallest `L` over all iterations is kept (lines 176-177). `solve_oracle` runs the bound twice, before and after the search, and reports the smaller (line 207). Each run is a valid bound, so their minimum is too.

## What the two numbers mean

`solve_oracle` returns:
- `value`: the value of a feasible schedule, which is at most the optimum;
- `upper`: a value that every schedule allowed by the night budget, the access windows and the costs cannot exceed.

The true optimum lies between them. Their difference is the reported gap.

This includes the tuned policies' schedules, which obey the same budget, windows and costs. It holds as long as the oracle's tables equal the simulator's accounting. `sr_tables` (lines 20-40) uses the simulator's update order, and R6 checked identical no-cleaning inputs.

The bound does not model the simulator's optional `battery_rows` and `availability` settings, which R6 and R7 do not use. With either set, the oracle's schedule could violate them, but the bound would still be an upper bound: those settings only remove schedules.

For the R7 information-restricted oracles (A, B, D), the plan is made on changed tables but scored in the simulator with the truth. Their bound refers to the changed problem and is not reported.
