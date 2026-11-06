import numpy as np
from pvclean import exact, model

CFG = model.merged(dict(n_rows=3, night_min=100.0, d0=120, d1=132, c_row=4.0))


def test_optimum_beats_no_cleaning_and_is_feasible():
    Rev = exact.row_tables(0, "fixed", CFG)
    res, sched = exact.solve(Rev, CFG, 60)
    assert res.status == 0 and exact.schedule_value(Rev, sched, CFG) >= exact.schedule_value(Rev, [], CFG) and model.schedule_violations(sched, CFG) == 0


def test_subsets_fit_the_night():
    assert all(model.mission_time(list(S), CFG) <= CFG["night_min"] for S in exact.feasible_subsets(CFG))


def test_belief_world_has_no_noise():
    c, v, _ = model.planner_inputs("fixed", CFG)
    w = exact.belief_world(c, v)
    assert np.all(w.exposure(CFG) == 1) and w.weather(0, CFG)["rain"].sum() == 0 and not w.rain_forecast(None, 0, CFG).any()


def test_receding_horizon_logs_solves():
    c, v, p = model.planner_inputs("fixed", CFG)
    lg = []
    model.simulate("mpc", {"fn": exact.make_mpc(horizon=4, log=lg)}, "fixed", 0, cfg=CFG, clim=c, vexp=v, pbar=p)
    assert lg and all(x["status"] == 0 for x in lg)
