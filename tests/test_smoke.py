"""End to end through the command line: the quickstart study, and a reload of its output. Needs no data."""
import json
import os
from pvclean.cli import main
from pvclean.data import repo_root


def test_quickstart_end_to_end(tmp_path, capsys):
    assert main(["run", os.path.join(repo_root(), "configs", "studies", "quickstart.yaml"), "--out", str(tmp_path)]) == 0
    r = json.load(open(tmp_path / "quickstart.json"))
    assert r["site"] == "dubai" and set(r["contracts"]) == {"fixed", "merchant"}
    assert all(v["row_cleanings"] >= 0 for c in r["contracts"].values() for v in c.values())
    assert "value of cleaning" in capsys.readouterr().out
