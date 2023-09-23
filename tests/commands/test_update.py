import os
import pytest
from typing import Any, Dict

import papis.database
from papis.document import Document

from papis.testing import TemporaryLibrary, PapisRunner, ResourceCache


def _get_resource_file(filename: str) -> str:
    resources = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "resources", "update"
    )
    filepath = os.path.join(resources, filename)
    assert os.path.exists(filepath)

    return filepath


def update_doc_from_data_interactively(
        document: Document,
        data: Dict[str, Any],
        data_name: str) -> None:
    document.update(data)


def test_update_run(tmp_library: TemporaryLibrary) -> None:
    from papis.commands.update import run

    db = papis.database.get()
    docs = db.get_all_documents()
    doc = docs[0]

    tags = "test_tag"
    run(doc, data={"tags": tags})

    doc, = db.query_dict({"tags": tags})
    assert doc["tags"] == tags


@pytest.mark.parametrize(("isbn", "doi"), [
    ("92130123", "10.213.phys.rev/213"),
    ("", "")
    ])
def test_update_cli(tmp_library: TemporaryLibrary, isbn: str, doi: str) -> None:
    from papis.commands.update import cli
    cli_runner = PapisRunner()

    result = cli_runner.invoke(
        cli,
        ["__no_document__"])
    assert result.exit_code == 0
    assert not result.output

    result = cli_runner.invoke(
        cli,
        ["--set", "isbn", isbn]
        + ["--set", "doi", doi, "krishnamurti"])
    assert result.exit_code == 0

    db = papis.database.get()
    doc, = db.query_dict({"author": "Krishnamurti"})
    assert doc["doi"] == doi
    assert doc["isbn"] == isbn


def test_update_yaml_cli(tmp_library: TemporaryLibrary,
                         resource_cache: ResourceCache,
                         monkeypatch: pytest.MonkeyPatch) -> None:
    from papis.commands.update import cli
    cli_runner = PapisRunner()

    filename = os.path.join(resource_cache.cachedir, "update", "russell.yaml")

    import papis.utils
    with monkeypatch.context() as m:
        m.setattr(papis.utils, "update_doc_from_data_interactively",
                  update_doc_from_data_interactively)

        result = cli_runner.invoke(
            cli,
            ["--from", "yaml", filename, "krishnamurti"])
        assert result.exit_code == 0

    import papis.yaml
    data = papis.yaml.yaml_to_data(filename)

    db = papis.database.get()
    doc, = db.query_dict({"author": "Russell"})

    assert doc["doi"] == data["doi"]


def test_update_bibtex_cli(tmp_library: TemporaryLibrary,
                           resource_cache: ResourceCache,
                           monkeypatch: pytest.MonkeyPatch) -> None:
    from papis.commands.update import cli
    cli_runner = PapisRunner()

    filename = os.path.join(resource_cache.cachedir, "update", "wannier.bib")

    import papis.utils
    with monkeypatch.context() as m:
        m.setattr(papis.utils, "update_doc_from_data_interactively",
                  update_doc_from_data_interactively)

        result = cli_runner.invoke(
            cli,
            ["--from", "bibtex", filename, "krishnamurti"])
        assert result.exit_code == 0

    import papis.bibtex
    data, = papis.bibtex.bibtex_to_dict(filename)

    db = papis.database.get()
    doc, = db.query_dict({"author": "Wannier"})

    assert doc["doi"] == data["doi"]


def test_update_cli_ref(tmp_library: TemporaryLibrary) -> None:
    from papis.commands.update import cli
    cli_runner = PapisRunner()

    result = cli_runner.invoke(
        cli,
        ["krishnamurti", "--set", "ref", "NewRef"])
    assert result.exit_code == 0
    assert not result.output

    db = papis.database.get()
    doc, = db.query_dict({"author": "krishnamurti"})
    assert doc["ref"] == "NewRef"
