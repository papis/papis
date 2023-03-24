import pytest

import papis.format
import papis.config
import papis.document

import tests.downloaders as testlib


@testlib.with_default_config
def test_python_formater(monkeypatch):
    papis.config.set("formater", "python")

    with monkeypatch.context() as m:
        m.setattr(papis.format, "_FORMATER", None)

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

        document = {"title": "The Phantom Menace"}
        assert (
            papis.format.format(
                "{doc[author]}: {doc[title]} ({doc[blahblah]})",
                document)
            == ": The Phantom Menace ()")


@testlib.with_default_config
def test_jinja_formater(monkeypatch):
    pytest.importorskip("jinja2")
    papis.config.set("formater", "jinja2")

    with monkeypatch.context() as m:
        m.setattr(papis.format, "_FORMATER", None)

        document = papis.document.from_data({"author": "Fulano", "title": "A New Hope"})
        assert (
            papis.format.format("{{ doc.author }}: {{ doc.title }}", document)
            == "Fulano: A New Hope")
        assert (
            papis.format.format("{{ doc. author }}:\\n\\t{{ doc.title }}", document)
            == "Fulano:\n\tA New Hope")
        assert (
            papis.format.format(
                "{{ doc.author }}: {{ doc.title }} - {{ doc.blahblah }}",
                document)
            == "Fulano: A New Hope - ")

        document = {"title": "The Phantom Menace"}
        assert (
            papis.format.format(
                "{{ doc.author }}: {{ doc.title }} ({{ doc.blahblah }})",
                document)
            == ": The Phantom Menace ()")
