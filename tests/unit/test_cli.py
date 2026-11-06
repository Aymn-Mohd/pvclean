import pytest
from pvclean.cli import main


def test_help_lists_commands(capsys):
    with pytest.raises(SystemExit):
        main(["--help"])
    out = capsys.readouterr().out
    assert all(w in out for w in ("run", "tune", "report", "download"))


def test_blocked_source_is_refused():
    with pytest.raises(SystemExit):
        main(["download", "bom"])
