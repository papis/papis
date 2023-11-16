import pytest

import papis.format
import papis.document

from papis.testing import TemporaryConfiguration


@pytest.mark.config_setup(settings={"formatter": "python"})
def test_python_formatter(tmp_config: TemporaryConfiguration) -> None:
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

    assert papis.format.format("{doc[title]!y}", data) == "the-phantom-menace"
    assert papis.format.format("{doc[title]:1.3S}", data) == "Phantom Menace"
    assert papis.format.format("{doc[title]:.2S}", data) == "The Phantom"
    assert papis.format.format("{doc[title]:2S}", data) == "The Phantom"


@pytest.mark.config_setup(settings={"formatter": "jinja2"})
def test_jinja_formatter(tmp_config: TemporaryConfiguration) -> None:
    pytest.importorskip("jinja2")

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
