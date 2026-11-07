import json
import pytest
from pvclean import download


def test_stops_at_first_block_and_records_it(monkeypatch, tmp_path):
    monkeypatch.setenv("PVCLEAN_DATA", str(tmp_path))
    calls = []
    monkeypatch.setitem(download.SOURCES, "fake", lambda: [dict(path=f"raw/f{i}", url=f"http://x/{i}", sha256="") for i in range(3)])
    monkeypatch.setattr(download, "fetch_once", lambda u: (calls.append(u), (403, b"blocked", "HTTP 403"))[1])
    r = download.download("fake")
    assert calls == ["http://x/0"], "one attempt, no retry, no next file"
    assert r["status"] == "stopped: HTTP 403" and r["files"][0]["http_status"] == 403 and r["files"][0]["sha256"]
    assert not (tmp_path / "raw" / "f0").exists()
    assert json.load(open(tmp_path / "provenance" / "fake.json"))["status"].startswith("stopped")


def test_success_writes_file_and_hash(monkeypatch, tmp_path):
    monkeypatch.setenv("PVCLEAN_DATA", str(tmp_path))
    monkeypatch.setitem(download.SOURCES, "fake", lambda: [dict(path="raw/a", url="http://x/a", sha256="")])
    monkeypatch.setattr(download, "fetch_once", lambda u: (200, b"abc", ""))
    r = download.download("fake")
    assert r["status"] == "ok" and (tmp_path / "raw" / "a").read_bytes() == b"abc" and len(r["files"][0]["sha256"]) == 64 and r["files"][0]["accessed"]


def test_cached_file_is_not_fetched(monkeypatch, tmp_path):
    monkeypatch.setenv("PVCLEAN_DATA", str(tmp_path))
    (tmp_path / "raw").mkdir(); (tmp_path / "raw" / "a").write_bytes(b"x")
    monkeypatch.setitem(download.SOURCES, "fake", lambda: [dict(path="raw/a", url="http://x/a", sha256="")])
    monkeypatch.setattr(download, "fetch_once", lambda u: pytest.fail("fetched a cached file"))
    assert download.download("fake")["files"][0]["accessed"] == "cached"


def test_unknown_source():
    with pytest.raises(SystemExit):
        download.download("bom")


def test_nasa_targets_carry_recorded_hashes():
    t = download.nasa_targets()
    assert len(t) == 200 and all(x["sha256"] for x in t)


def test_sites_filter_drops_only_the_failed_site(tmp_path, monkeypatch):
    monkeypatch.setenv("PVCLEAN_DATA", str(tmp_path))
    calls = []
    monkeypatch.setitem(download.SOURCES, "fake", lambda: [dict(path=f"raw/{s}{i}", url=f"http://x/{s}{i}", sha256="", site=s) for s in "ab" for i in range(2)])
    monkeypatch.setattr(download, "fetch_once", lambda u: (calls.append(u), (500, b"", "HTTP 500") if u.endswith("a0") else (200, b"ok", ""))[1])
    r = download.download("fake", sites=["a", "b"])
    assert calls == ["http://x/a0", "http://x/b0", "http://x/b1"] and r["dropped_sites"] == ["a"]


def test_sites_filter_stops_on_a_block(tmp_path, monkeypatch):
    monkeypatch.setenv("PVCLEAN_DATA", str(tmp_path))
    calls = []
    monkeypatch.setitem(download.SOURCES, "fake", lambda: [dict(path=f"raw/{s}", url=f"http://x/{s}", sha256="", site=s) for s in "ab"])
    monkeypatch.setattr(download, "fetch_once", lambda u: (calls.append(u), (403, b"", "HTTP 403"))[1])
    download.download("fake", sites=["a", "b"])
    assert calls == ["http://x/a"]
