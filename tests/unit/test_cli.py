import pytest

from lonekrav.etl import cli


def test_help_lists_every_subcommand(capsys):
    with pytest.raises(SystemExit) as e:
        cli.main(["--help"])
    assert e.value.code == 0
    out = capsys.readouterr().out
    for cmd in ("fetch", "build", "index", "benchmark", "measure-models"):
        assert cmd in out


def test_unknown_fetch_source_exits_1_with_message(capsys):
    assert cli.main(["fetch", "--only", "nope"]) == 1
    assert "unknown source 'nope'" in capsys.readouterr().err


def test_step_failure_exits_1_with_one_line_cause(capsys, monkeypatch):
    def boom(args):
        raise RuntimeError("scb_pxweb: download failed for https://x")

    monkeypatch.setitem(cli.COMMANDS, "build", boom)
    assert cli.main(["build"]) == 1
    assert capsys.readouterr().err.strip() == "error: scb_pxweb: download failed for https://x"
