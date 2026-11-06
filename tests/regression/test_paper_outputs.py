"""Regenerates every papers/e1_pes/numbers*.tex, table_*.tex and results/macros_*.json from the stored results into a temporary directory, and compares them byte for byte
with the files in the repository. With the data cache absent this still runs: the data-derived numbers come from results/macro_inputs.json."""
import filecmp, glob, os
import pytest
from pvclean.data import repo_root
from pvclean.reporting import build_all

ROOT = repo_root()
PAPER = os.path.join(ROOT, "papers", "e1_pes")
RECORDS = os.path.join(ROOT, "docs", "records")
TEX = sorted(os.path.basename(f) for f in glob.glob(os.path.join(PAPER, "numbers*.tex")) + glob.glob(os.path.join(PAPER, "table_*.tex")))
MACROS = sorted(os.path.basename(f) for f in glob.glob(os.path.join(ROOT, "results", "macros_*.json")))
SUMMARIES = ["R1_SUMMARY.md", "R2_SUMMARY.md", "R3_SUMMARY.md", "CLAIMS_REGISTRY.md"]


@pytest.fixture(scope="module")
def regenerated(tmp_path_factory):
    t = tmp_path_factory.mktemp("paper")
    build_all(out=str(t / "paper"), results_out=str(t / "res"), figures=False, summaries=True, docs=str(t / "docs"))
    return t


def test_files_found():
    assert len(TEX) == 7 and len(MACROS) == 2


@pytest.mark.parametrize("name", TEX)
def test_tex(regenerated, name):
    assert filecmp.cmp(os.path.join(PAPER, name), regenerated / "paper" / name, shallow=False), name


@pytest.mark.parametrize("name", MACROS)
def test_macros(regenerated, name):
    assert filecmp.cmp(os.path.join(ROOT, "results", name), regenerated / "res" / name, shallow=False), name


@pytest.mark.parametrize("name", SUMMARIES)
def test_summaries(regenerated, name):
    assert filecmp.cmp(os.path.join(RECORDS, name), regenerated / "docs" / name, shallow=False), name


def test_macro_inputs_match_data(data_available):
    if not data_available:
        pytest.skip("data not in the cache")
    import json
    from pvclean.reporting.inputs import compute
    assert compute(json.load(open(os.path.join(ROOT, "results", "results.json")))["config"]) == json.load(open(os.path.join(ROOT, "results", "macro_inputs.json")))
