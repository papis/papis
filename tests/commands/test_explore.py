from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
from typing import Any, cast

import pytest

from papis.testing import PapisRunner, TemporaryLibrary


def _explore_export(tmp_library: TemporaryLibrary,
                    chain: list[str],
                    outname: str) -> list[dict[str, object]]:
    # NOTE: Tests use this function not to check if JSON export is correct, but rather
    # to check whether the explorer's internal data processing is correct.
    from papis.commands.explore import cli

    outfile = os.path.join(tmp_library.tmpdir, outname)
    result = PapisRunner().invoke(
        cli, [*chain, "export", "--format", "json", "--out", outfile])
    assert result.exit_code == 0

    with open(outfile, encoding="utf-8") as fd:
        return cast("list[dict[str, object]]", json.load(fd))


def test_explore_cli(tmp_library: TemporaryLibrary) -> None:
    from papis.commands.explore import cli
    cli_runner = PapisRunner()

    result = cli_runner.invoke(
        cli,
        ["cmd", "ls"])
    assert result.exit_code == 0

    result = cli_runner.invoke(
        cli,
        ["lib", "krishnamurti"])
    assert result.exit_code == 0


def test_explore_bibtex_cli(tmp_library: TemporaryLibrary) -> None:
    from papis.commands.explore import cli
    cli_runner = PapisRunner()

    with tempfile.NamedTemporaryFile(delete=False, dir=tmp_library.tmpdir) as f:
        path = f.name

    result = cli_runner.invoke(
        cli,
        ["lib", "krishnamurti", "export", "--format", "bibtex", "--out", path])
    assert result.exit_code == 0

    with open(path, encoding="utf-8") as fd:
        exported_bibtex = fd.read()

    assert exported_bibtex == (
        "@article{Freedom_from_th_J_Kri_2009,\n"
        "  author = {J. Krishnamurti},\n"
        "  title = {Freedom from the known},\n"
        "  year = {2009},\n"
        "}"
    )


def test_explore_yaml_cli(tmp_library: TemporaryLibrary) -> None:
    from papis.commands.explore import cli
    cli_runner = PapisRunner()

    with tempfile.NamedTemporaryFile(delete=False, dir=tmp_library.tmpdir) as f:
        path = f.name

    result = cli_runner.invoke(
        cli,
        ["lib", "popper", "export", "--format", "yaml", "--out", path])
    assert result.exit_code == 0

    with open(path, encoding="utf-8") as fd:
        exported_yaml = fd.read()

    assert re.match(
        r"---\n"
        r"author: K. Popper\n"
        r"doi: 10.1021/ct5004252\n"
        r"papis_id: .*\n"
        r"title: The open society\n"
        r"volume: I\n",
        exported_yaml
    )


def test_explore_citations_and_json_cli(tmp_library: TemporaryLibrary) -> None:
    from papis.commands.explore import cli
    cli_runner = PapisRunner()

    with tempfile.NamedTemporaryFile(delete=False, dir=tmp_library.tmpdir) as f:
        path = f.name

    result = cli_runner.invoke(
        cli,
        ["citations", "krishnamurti", "export", "--format", "json", "--out", path])
    assert result.exit_code == 0

    with open(path, encoding="utf-8") as fd:
        exported_json = fd.read()

    assert exported_json == "[]"


def test_explore_cmd_batch(tmp_library: TemporaryLibrary) -> None:
    from papis.commands.explore import cli
    cli_runner = PapisRunner()

    result = cli_runner.invoke(
        cli,
        ["lib", "krishnamurti", "cmd", "--batch", "sh -c 'exit 1'"])
    assert result.exit_code == 0

    with pytest.raises(subprocess.CalledProcessError):
        cli_runner.invoke(
            cli,
            ["lib", "krishnamurti", "cmd", "sh -c 'exit 1'"])


@pytest.mark.parametrize(("explorer", "target"), [
    ("crossref", "papis.explorers.crossref"),
    ("arxiv", "papis.arxiv"),
    ("dblp", "papis.dblp"),
    ("isbn", "papis.explorers.isbn"),
    ])
def test_explore_source_error(tmp_library: TemporaryLibrary,
                              monkeypatch: pytest.MonkeyPatch,
                              explorer: str,
                              target: str) -> None:
    """A failed source query is logged and does not abort the command."""
    import importlib

    from papis.exceptions import SourceError

    module = importlib.import_module(f"papis.explorers.{explorer}")
    target_module = importlib.import_module(target)

    def get_data(**kwargs: Any) -> Any:
        raise SourceError("boom")

    monkeypatch.setattr(target_module, "get_data", get_data)

    result = PapisRunner().invoke(module.cli, ["-q", "test"])
    assert result.exit_code == 0


def test_explore_bibtex_file_cli(tmp_library: TemporaryLibrary) -> None:
    """BibTeX files are exported to documents with normalized author lists."""
    bibfile = os.path.join(tmp_library.tmpdir, "test.bib")
    with open(bibfile, "w", encoding="utf-8") as fd:
        fd.write(
            "@article{test,\n"
            "  author = {D. Bohm},\n"
            "  title = {Quantum Theory}\n"
            "}\n")

    data = _explore_export(tmp_library, ["bibtex", bibfile], "bibtex_out.json")

    assert len(data) == 1
    assert data[0]["title"] == "Quantum Theory"
    assert data[0]["author"] == "Bohm, D."


def test_explore_yaml_file_cli(tmp_library: TemporaryLibrary) -> None:
    """YAML files are exported."""
    yamlfile = os.path.join(tmp_library.tmpdir, "test.yaml")
    with open(yamlfile, "w", encoding="utf-8") as fd:
        fd.write("author: Tolkien\ntitle: The lord of the rings\n")

    data = _explore_export(tmp_library, ["yaml", yamlfile], "yaml_out.json")

    assert len(data) == 1
    assert data[0]["title"] == "The lord of the rings"
    assert data[0]["author"] == "Tolkien"


def test_explore_json_file_cli(tmp_library: TemporaryLibrary) -> None:
    """JSON files are exported."""
    jsonfile = os.path.join(tmp_library.tmpdir, "test.json")
    with open(jsonfile, "w", encoding="utf-8") as fd:
        json.dump([{"author": "Bohm", "title": "Quantum Theory"}], fd)

    data = _explore_export(tmp_library, ["json", jsonfile], "json_out.json")

    assert len(data) == 1
    assert data[0]["title"] == "Quantum Theory"
    assert data[0]["author"] == "Bohm"
