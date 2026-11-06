import numpy as np
from pvclean import model
from pvclean.core import robot

C = model.CONFIG


def test_mission_time():
    assert robot.mission_time([], C) == 0.0
    assert robot.mission_time([1, 3], C) == 2 * 10.0 * 4 / 0.5 / 60.0 + 25.0 * 2


def test_pack_respects_night_and_battery():
    assert robot.mission_time(robot.pack(list(range(40)), C), C) <= C["night_min"]
    assert len(robot.pack(list(range(40)), dict(C, battery_rows=3))) == 3


def test_blackout_closes_odd_rows_only():
    m = robot.blackout_mask(C)
    assert m[60, 1] and not m[60, 0] and not m[59, 1] and m.sum() == 15 * 20


def test_availability_only_adds_down_nights():
    a = robot.robot_up(1, dict(C, availability=0.9)); b = robot.robot_up(1, dict(C, availability=0.8))
    assert np.all(a[b]) and b.sum() < a.sum()


def test_violations_counted():
    assert robot.schedule_violations([(10, [0, 1])], C) == 0
    assert robot.schedule_violations([(61, [1])], C) == 1            # closed row
    assert robot.schedule_violations([(10, [1]), (10, [2])], C) == 1  # two missions in a night


def test_mission_record_stops_ascend():
    r = robot.mission_record(3, [5, 2], [], "x", C)
    assert r["rows"] == [2, 5] and r["stops"][0]["arrive_min"] < r["stops"][1]["arrive_min"] and r["end_min"] == robot.mission_time([5, 2], C)
