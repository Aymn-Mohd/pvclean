"""Every study type must reproduce its golden file byte for byte. If one fails, fix the code, never the golden file."""
import os
import pytest
import cases

GOLDEN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "golden")


@pytest.mark.parametrize("name", list(cases.CASES))
def test_golden(name, data_available):
    if name in cases.NEEDS_DATA and not data_available:
        pytest.skip("market and weather data not in the cache: run `python -m pvclean download`")
    got = cases.text(cases.CASES[name]())
    want = open(os.path.join(GOLDEN, f"{name}.json")).read()
    assert got == want, f"{name}: output differs from its golden file"
