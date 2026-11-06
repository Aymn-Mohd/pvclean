"""Rules of the repository that a test can check."""
import os
import re
import subprocess
from pvclean.data import repo_root

ROOT = repo_root()
BANNED = re.compile(r"\b(framework|platform|ecosystem|vision|roadmap|future plans)\b", re.I)


def tracked():
    return subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True).stdout.split("\n")


def test_wording():
    bad = []
    for f in tracked():
        if f.endswith((".md", ".py", ".yaml", ".toml", ".sh")) and not f.startswith(("docs/records/", "legacy/", "tests/test_repo_rules.py", "papers/")):
            for i, l in enumerate(open(os.path.join(ROOT, f), errors="ignore"), 1):
                if BANNED.search(l):
                    bad.append(f"{f}:{i}")
    assert not bad, bad


def test_no_data_or_large_binaries():
    bad = [f for f in tracked() if f and (f.endswith((".npz", ".csv", ".csv.gz", ".parquet")) or (f.startswith("data/") and not f.startswith("data/provenance/")))]
    assert not bad, bad
    big = [f for f in tracked() if f and not f.startswith("results/") and os.path.getsize(os.path.join(ROOT, f)) > 2_000_000]
    assert not big, big


def test_readme_has_no_em_dash():
    assert "—" not in open(os.path.join(ROOT, "README.md")).read()
