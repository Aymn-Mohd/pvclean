"""The only file in tests/regression that knows where the code lives. Moves change this file; golden files never change."""
from types import SimpleNamespace
from pvclean import forecasts, model as sim
from pvclean.config import load_protocol
from pvclean.core.soiling import expected_increment
from pvclean.exact import belief_world, make_mpc, row_tables, schedule_value, solve
from pvclean.studies import chrono, matched as mr, robot_sweep as rs
from pvclean.studies.runner import Runner

forecasting = forecasts
checks = sim
exact = SimpleNamespace(row_tables=row_tables, solve=solve, schedule_value=schedule_value, expected_increment=expected_increment, make_mpc=lambda h: make_mpc(horizon=h))
optimisation = SimpleNamespace(make_mpc=make_mpc)


def runner(pool, train, test, grid):
    p = load_protocol()
    return Runner(p.with_(train=train, test=test, grids={**p.grids, **grid}), pool)
