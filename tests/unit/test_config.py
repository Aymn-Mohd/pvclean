import pytest
from pvclean import config


def test_merged_does_not_change_defaults():
    c = config.merged({"c_row": 9.0})
    assert c["c_row"] == 9.0 and config.CONFIG["c_row"] == 4.0


def test_grid_order_is_first_key_outermost():
    assert config.grid({"a": [1, 2], "b": [3, 4]}) == [{"a": 1, "b": 3}, {"a": 1, "b": 4}, {"a": 2, "b": 3}, {"a": 2, "b": 4}]


def test_seeds_forms():
    assert config.seeds({"start": 2, "stop": 4}) == [2, 3] and config.seeds([7, 8]) == [7, 8]


def test_protocol_override_replaces_one_grid_only():
    p = config.load_protocol({"grids": {"econ": {"b": [3]}}, "train_seeds": [1]})
    assert p.grids["econ"] == [{"b": 3}] and len(p.grids["fixed"]) == 9 and p.train == [1]


def test_protocol_copies_are_independent():
    p = config.load_protocol(); q = p.with_(train=[5])
    assert p.train == [1000, 1001, 1002, 1003, 1004] and q.train == [5]


@pytest.mark.parametrize("k", config.STORED_CONFIG_KEYS)
def test_stored_keys_exist(k):
    assert k in config.CONFIG
