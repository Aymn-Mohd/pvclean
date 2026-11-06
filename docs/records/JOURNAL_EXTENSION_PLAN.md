# Journal extension plan (kept separate from the conference paper)

Target: Applied Energy, Solar Energy or Renewable Energy (decide after the PES decision). **Before submission, read the journal's prior-publication
policy**: a conference paper is normally allowed as a precursor if the journal paper adds substantial new material, cites the conference paper and
discloses the overlap in the cover letter; some journals ask for a stated percentage of new content. Cite the conference paper
("Mohammed, Nassereddine, … , *When Does Contract-Aware PV Cleaning Planning Pay?*, IEEE PES General Meeting 2027") as the precursor. This plan lists only
material that is **not** in the 5-page paper and is **not** claimed there.

| Block | New content | Needed data / work | Status |
|---|---|---|---|
| J1 Rover measurements | Travel energy, inspection duration and cleaning effectiveness measured on the half-scale rover (Jan–Feb 2027 testing) replace the assumed 25 min/row, 0.5 m/s, 0.995 residual | rover logs; protocol with repeat runs and uncertainty | not started |
| J2 Inspection-energy calibration | Energy and time per inspection patrol as a function of row length and sensor payload; closes the open loop on `c_insp` and the mobile-information value | rover power logs | not started |
| J3 Real soiling estimation | Estimate soiling from measured data (RdTools stochastic rate-and-recovery on reference-cell or string data; RdTools gives site/plant-level soiling, **not** row-level) and fit row exposure from patrol measurements | at least one measured Dubai soiling series; none is available today | blocked on data |
| J4 Larger optimality studies | Receding-horizon MILP at 10–40 rows with decomposition (Lagrangian / column generation), certified gaps, horizon ≥ 30 d with terminal value (see EXP-03/04), rolling-horizon vs. clairvoyant on more instances and seasons | compute; Pyomo + HiGHS or Gurobi/CPLEX if licensed | partly prototyped (v10) |
| J5 Stochastic MPC | Scenario-based two-stage / multistage MPC over dust, rain and price scenarios; value of the stochastic solution vs. expected-value MPC | scenario generator; calibrated dust model | not started |
| J6 Spatial value of information | Row-level information (exposure gradient, patrol frequency) priced against inspection cost; spatial sampling design | J1–J3 | not started |
| J7 Agrivoltaic access constraints | Real crop calendars and machinery schedules instead of three fixed 5-day windows; farm-side cost of robot downtime | farm partner data | not started |
| J8 Longer and more markets | ≥ 8–10 price years per market (e.g. 2016–2025), more regions, forward-chaining (expanding-window) validation so that all forecast scenarios are causal; hierarchical models with market as a random effect | additional AEMO/OMIE/ERCOT/CAISO downloads | not started |
| J9 More contracts | Time-of-use, capacity payments, hybrid PPA + merchant tail, curtailment compensation, battery co-optimisation | contract terms | not started |
| J10 Cost model | Crew vs. robot cost, water and labour prices, degradation from repeated cleaning, uncertainty in `c_row` and `c_mission` | supplier quotes | not started |

Out of scope for the conference paper and **not** to be implied by it: any claim about measured soiling at a real plant, any claim that the heuristics are
near-optimal at full scale, any population-level statement about electricity markets.
