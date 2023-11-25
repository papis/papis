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

    # test out a jinja2 format
    from papis.strings import FormattedString
    assert len(papis.format.FORMATTER) == 1
    assert (
        papis.format.format(
            FormattedString("jinja2", "{{ doc.author }}: {{ doc.title }}"),
            document)
        == "Fulano: A New Hope")
    assert len(papis.format.FORMATTER) == 2


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

    # test out a python format
    assert len(papis.format.FORMATTER) == 1
    from papis.strings import FormattedString
    assert (
        papis.format.format(
            FormattedString("python", "{doc[author]}: {doc[title]}"),
            document)
        == "Fulano: A New Hope")
    assert len(papis.format.FORMATTER) == 2


def test_overwritten_keys(tmp_config: TemporaryConfiguration) -> None:
    pytest.importorskip("jinja2")

    import papis.config

    papis.config.set("ref-format.jinja2", "{{ doc.author|lower }}{{ doc.year }}")
    document = papis.document.from_data({
        "author": "Fulano", "year": 2020, "title": "A New Hope"
    })

    fmt = papis.config.getformattedstring("ref-format")
    assert fmt.formatter == "jinja2"

    ref = papis.format.format(fmt, document)
    assert ref == "fulano2020"

    from papis.bibtex import create_reference

    ref = create_reference(document, force=True)
    assert ref == "fulano2020"
