import pytest

import papis.format
import papis.config
import papis.document

from tests.testlib import TemporaryConfiguration


def test_python_formater(tmp_config: TemporaryConfiguration, monkeypatch) -> None:
    papis.config.set("formater", "python")
    monkeypatch.setattr(papis.format, "FORMATER", None)

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


def test_jinja_formater(tmp_config: TemporaryConfiguration, monkeypatch) -> None:
    pytest.importorskip("jinja2")
    papis.config.set("formater", "jinja2")
    monkeypatch.setattr(papis.format, "FORMATER", None)

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

def test_local_formater(tmp_config: TemporaryConfiguration, monkeypatch) -> None:
    for global_formater in ['jinja2', 'python']:
        if global_formater == 'jinja2':
            pytest.importorskip("jinja2")
        monkeypatch.setattr(papis.format, "FORMATER", None)
        papis.config.set("formater", global_formater)

        document = papis.document.from_data({"author": "Fulano", "title": "A New Hope"})
        data = {"title": "The Phantom Menace"}
        # Python
        assert (
            papis.format.format("[python]{doc[author]}: {doc[title]}", document)
            == "Fulano: A New Hope")
        assert (
            papis.format.format("[python]{doc[author]}:\\n\\t»{doc[title]}", document)
            == "Fulano:\n\t»A New Hope")
        assert (
            papis.format.format(
                "[python]{doc[author]}: {doc[title]} - {doc[blahblah]}",
                document)
            == "Fulano: A New Hope - ")

        assert (
            papis.format.format(
                "[python]{doc[author]}: {doc[title]} ({doc[blahblah]})",
                data)
            == ": The Phantom Menace ()")

        # Jinja2
        assert (
            papis.format.format("[jinja2]{{ doc.author }}: {{ doc.title }}", document)
            == "Fulano: A New Hope")
        assert (
            papis.format.format("[jinja2]{{ doc. author }}:\\n\\t»{{ doc.title }}", document)
            == "Fulano:\n\t»A New Hope")
        assert (
            papis.format.format(
                "[jinja2]{{ doc.author }}: {{ doc.title }} - {{ doc.blahblah }}",
                document)
            == "Fulano: A New Hope - ")

        assert (
            papis.format.format(
                "[jinja2]{{ doc.author }}: {{ doc.title }} ({{ doc.blahblah }})",
                data)
            == ": The Phantom Menace ()")

