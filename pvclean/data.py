"""Where market and weather data live. Nothing here is in git: the cache is $PVCLEAN_DATA, or ~/.cache/pvclean/data."""
from __future__ import annotations
import os


def data_dir() -> str:
    """The data cache directory."""
    return os.environ.get("PVCLEAN_DATA") or os.path.join(os.path.expanduser("~"), ".cache", "pvclean", "data")


def data_path(*parts: str) -> str:
    """A path inside the data cache."""
    return os.path.join(data_dir(), *parts)


def repo_root() -> str:
    """The checkout that holds this package, or the working directory if it is installed elsewhere."""
    root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    return root if os.path.isdir(os.path.join(root, "configs")) else os.getcwd()


def results_dir() -> str:
    """Stored results: $PVCLEAN_RESULTS, or results/ in the checkout."""
    return os.environ.get("PVCLEAN_RESULTS") or os.path.join(repo_root(), "results")


def has_data(*names: str) -> bool:
    """True if every named file is in the cache."""
    return all(os.path.exists(data_path(n)) for n in names)
