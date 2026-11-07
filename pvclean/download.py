"""Downloads into the data cache. One attempt per URL: no retries, no changed headers and no other route around a block. Every attempt is recorded with URL, sha256 and access date."""
from __future__ import annotations
import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from typing import Any
from pvclean.data import data_dir, data_path, repo_root

USER_AGENT = "pvclean-research-client"
NASA_API = "https://power.larc.nasa.gov/api/temporal/hourly/point"
NASA_PARAMS = "ALLSKY_SFC_SW_DWN,ALLSKY_SFC_SW_DNI,ALLSKY_SFC_SW_DIFF,CLRSKY_SFC_SW_DWN,T2M,WS10M,PRECTOTCORR"
NASA_SITES = {"adelaide": (-34.93, 138.60), "brisbane": (-27.47, 153.03), "seville": (37.39, -5.99),
              "almeria": (36.84, -2.46), "cordoba": (37.88, -4.78), "bilbao": (43.26, -2.93), "port_augusta": (-32.49, 137.77), "longreach": (-23.44, 144.25)}
NASA_RECORDS = ("r3_nasa_power.json", "r4_nasa_power.json")
NASA_YEARS = range(2001, 2026)


def nasa_url(lat: float, lon: float, y: int) -> str:
    """The request URL of one site-year."""
    return f"{NASA_API}?parameters={NASA_PARAMS}&community=RE&longitude={lon}&latitude={lat}&start={y}0101&end={y}1231&format=CSV&time-standard=UTC"


def nasa_targets() -> list[dict[str, str]]:
    """NASA POWER site-years, with expected hashes where the repository records them."""
    known: dict[str, str] = {}
    for name in NASA_RECORDS:
        path = os.path.join(repo_root(), "data", "provenance", name)
        if os.path.exists(path):
            known.update({f["path"]: f["sha256"] for f in json.load(open(path))["files"]})
    return [dict(path=f"raw/nasa_power/{s}_{y}.csv", url=nasa_url(lat, lon, y), sha256=known.get(f"data/raw/nasa_power/{s}_{y}.csv", ""), site=s) for s, (lat, lon) in NASA_SITES.items() for y in NASA_YEARS]


def listed_targets(prefix: str) -> list[dict[str, str]]:
    """Files of data/provenance/r1_downloads.json under data/raw/<prefix>/ with a real URL."""
    files = json.load(open(os.path.join(repo_root(), "data", "provenance", "r1_downloads.json")))["files"]
    return [dict(path=f["path"][len("data/"):], url=f["url"], sha256=f["sha256"]) for f in files if f["path"].startswith(f"data/raw/{prefix}/") and f["url"].startswith("http")]


SOURCES = {"nasa-power": nasa_targets, "aemo": lambda: listed_targets("aemo"), "omie": lambda: listed_targets("omie")}


def fetch_once(url: str) -> tuple[int, bytes, str]:
    """One request. Returns (HTTP status, body, error text)."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            return r.status, r.read(), ""
    except urllib.error.HTTPError as e:
        return e.code, e.read(), f"HTTP {e.code}"
    except OSError as e:
        return 0, b"", repr(e)


def download(source: str, limit: int | None = None, sites: list[str] | None = None) -> dict[str, Any]:
    """Fetches the files of one source that the cache lacks. Stops at the first failed request, because a block applies to the whole source. With `sites`, only those sites are
    fetched, and a failure other than HTTP 403 or 429 drops the rest of that site and moves to the next one. A failed URL is not requested again."""
    if source not in SOURCES:
        raise SystemExit(f"unknown source {source}; known: {', '.join(SOURCES)}")
    rows: list[dict[str, Any]] = []; status = "ok"
    today = time.strftime("%Y-%m-%d"); dropped: list[str] = []
    targets = SOURCES[source]()
    if sites:
        targets = [t for t in targets if t.get("site") in sites]
    for t in targets[:limit]:
        if t.get("site") in dropped:
            continue
        path = data_path(t["path"])
        if os.path.exists(path):
            b = open(path, "rb").read()
            rows.append(dict(path=t["path"], url=t["url"], bytes=len(b), sha256=hashlib.sha256(b).hexdigest(), expected_sha256=t["sha256"], accessed="cached"))
            continue
        code, b, err = fetch_once(t["url"])
        row = dict(path=t["path"], url=t["url"], http_status=code, bytes=len(b), sha256=hashlib.sha256(b).hexdigest(), expected_sha256=t["sha256"], accessed=today)
        rows.append(row)
        if err or code != 200:
            row["error"] = err or f"HTTP {code}"; status = "stopped: " + row["error"]
            if sites and code not in (403, 429):
                dropped.append(t["site"]); continue
            break
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path + ".part", "wb") as f:
            f.write(b)
        os.replace(path + ".part", path)
    out = dict(source=source, status=status, files=rows, cache=data_dir(), dropped_sites=dropped)
    os.makedirs(data_path("provenance"), exist_ok=True)
    json.dump(out, open(data_path("provenance", f"{source}.json"), "w"), indent=1)
    return out
