"""Runs `pvclean report` in a copy of the repository, then the full test suite in that same folder."""
import os
import shutil
import subprocess
import sys
import pytest
from pvclean.data import repo_root

ROOT = repo_root()
THIS = "tests/test_report_then_suite.py::test_suite_passes_after_report"


def run(cmd, cwd, env=None):
    return subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True)


def test_suite_passes_after_report(tmp_path):
    listed = run(["git", "ls-files"], ROOT)
    files = [f for f in listed.stdout.split("\n") if f] if listed.returncode == 0 else []
    if not files:
        pytest.skip("needs a git checkout")
    dst = tmp_path / "repo"
    for f in files:
        (dst / f).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(os.path.join(ROOT, f), dst / f)
    assert run(["git", "init", "-q"], dst).returncode == 0
    assert run(["git", "add", "-A"], dst).returncode == 0
    env = dict(os.environ, PYTHONPATH=str(dst))
    r = run([sys.executable, "-m", "pvclean", "report"], dst, env)
    assert r.returncode == 0, r.stderr[-2000:]
    assert run(["git", "ls-files", "--others", "--exclude-standard"], dst).stdout == ""
    assert run(["git", "diff", "--name-only", "--", "papers", "results/macros_pes.json", "results/macros_v10.json"], dst).stdout == ""
    r = run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--deselect", THIS], dst, env)
    assert r.returncode == 0, r.stdout[-2000:]
