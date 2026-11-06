import glob
import os
import pytest
from pvclean.data import repo_root
from pvclean.studies import RUNNERS, load_study, runner_function
from pvclean.studies.runner import Runner, over_key
from pvclean.config import load_protocol
from multiprocessing import Pool

CONFIGS = sorted(glob.glob(os.path.join(repo_root(), "configs", "studies", "*.yaml")))


@pytest.mark.parametrize("path", CONFIGS, ids=[os.path.basename(c) for c in CONFIGS])
def test_every_config_names_a_runner(path, tmp_path):
    S = load_study(path, str(tmp_path))
    assert S.runner in RUNNERS and S.output.endswith(".json") and callable(runner_function(S.runner))


def test_default_output_is_not_the_stored_results():
    S = load_study(os.path.join(repo_root(), "configs", "studies", "quickstart.yaml"))
    assert S.out_dir.endswith(os.path.join("runs", "quickstart"))


def test_with_shares_the_pool_and_keeps_the_original():
    r = Runner(load_protocol(), pool="p")
    q = r.with_(train=[1])
    assert q.pool == "p" and q.train == [1] and r.train[0] == 1000


def test_results_do_not_depend_on_worker_count():
    p = load_protocol({"train_seeds": [1000], "test_seeds": [0, 1], "grids": {"fixed": {"T": [14, 28]}}})
    over = dict(n_rows=6, night_min=100.0, d0=120, d1=150)
    out = []
    for n in (1, 3):
        with Pool(n) as pool:
            out.append(Runner(p, pool).tune("fixed", over, ["fixed"]))
    assert out[0] == out[1]


def test_over_key_is_stable():
    assert over_key({"b": 1, "a": 2}) == over_key({"a": 2, "b": 1})
