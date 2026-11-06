from pvclean.reporting.macros import rnd


def test_half_up():
    assert rnd(0.5) == "1" and rnd(1.5) == "2" and rnd(2.5) == "3" and rnd(-2.5) == "-3" and rnd(1.005, 2) == "1.01"
