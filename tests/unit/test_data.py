from pvclean import data


def test_env_overrides_cache(monkeypatch, tmp_path):
    monkeypatch.setenv("PVCLEAN_DATA", str(tmp_path))
    assert data.data_path("a", "b") == str(tmp_path / "a" / "b")
    assert not data.has_data("missing.npz")
    (tmp_path / "x").write_text("1")
    assert data.has_data("x")


def test_results_env(monkeypatch):
    monkeypatch.setenv("PVCLEAN_RESULTS", "/r")
    assert data.results_dir() == "/r"
