import pytest

import papis.format
import papis.document

from papis.testing import TemporaryConfiguration


@pytest.mark.config_setup(settings={"formatter": "python"})
def test_python_formatter(tmp_config: TemporaryConfiguration, monkeypatch) -> None:
    monkeypatch.setattr(papis.format, "FORMATTER", None)

    document = papis.document.from_data({"author": "Fulano", "title": "A New Hope"})
    assert (
        papis.format.format("{doc[author]}: {doc[title]}", document)
        == "Fulano: A New Hope")
    assert (
        papis.format.format("{doc[author]}:\\n\\t»{doc[title]}", document)
        == "Fulano:\n\t»A New Hope")
    assert (
        papis.format.format(
            "{doc[author]}: {doc[title]} - {doc[blahblah]}",
            document)
        == "Fulano: A New Hope - ")

    data = {"title": "The Phantom Menace"}
    assert (
        papis.format.format(
            "{doc[author]}: {doc[title]} ({doc[blahblah]})",
            data)
        == ": The Phantom Menace ()")


@pytest.mark.config_setup(settings={"formatter": "jinja2"})
def test_jinja_formatter(tmp_config: TemporaryConfiguration, monkeypatch) -> None:
    pytest.importorskip("jinja2")
    monkeypatch.setattr(papis.format, "FORMATTER", None)

    document = papis.document.from_data({"author": "Fulano", "title": "A New Hope"})
    assert (
        papis.format.format("{{ doc.author }}: {{ doc.title }}", document)
        == "Fulano: A New Hope")
    assert (
        papis.format.format("{{ doc. author }}:\\n\\t»{{ doc.title }}", document)
        == "Fulano:\n\t»A New Hope")
    assert (
        papis.format.format(
            "{{ doc.author }}: {{ doc.title }} - {{ doc.blahblah }}",
            document)
        == "Fulano: A New Hope - ")

    data = {"title": "The Phantom Menace"}
    assert (
        papis.format.format(
            "{{ doc.author }}: {{ doc.title }} ({{ doc.blahblah }})",
            data)
        == ": The Phantom Menace ()")
