"""CLI smoke tests (against the fixture registry via monkeypatched REGISTRY)."""
import pytest

import rheodata
import rheodata.cli as cli_mod
from rheodata.cli import install_skill, main


@pytest.fixture()
def fixture_registry_active(fixture_registry, monkeypatch):
    monkeypatch.setattr(rheodata, "REGISTRY", dict(fixture_registry))
    monkeypatch.setattr(cli_mod.rheodata, "REGISTRY", dict(fixture_registry))


def test_cli_list(fixture_registry_active, capsys):
    assert main(["list"]) == 0
    out = capsys.readouterr().out
    assert "flow_curve_demo" in out


def test_cli_search(fixture_registry_active, capsys):
    assert main(["search", "--material", "synthetic", "--experiment", "flow_curve"]) == 0
    out = capsys.readouterr().out
    assert "flow_curve_demo" in out
    assert main(["search", "--query", "zzz_no_such"]) == 0
    assert "(no datasets match)" in capsys.readouterr().out


def test_cli_info(fixture_registry_active, capsys):
    assert main(["info", "freq_sweep_demo"]) == 0
    assert "https://doi.org/" in capsys.readouterr().out
    assert main(["info", "no_such_id"]) == 1


def test_cli_install_skill(tmp_path):
    dest = install_skill(dest_dir=tmp_path)
    assert (dest / "SKILL.md").is_file()
