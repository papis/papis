from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from papis.sources.handler import LookupInput
from papis.sources.handlers.formats.bibtex import BibTeXHandler
from papis.sources.handlers.formats.json import JsonHandler
from papis.sources.handlers.formats.yaml import YamlHandler

if TYPE_CHECKING:
    from papis.sources.handler import SourceHandler
    from papis.sources.handlers.formats import ContentFormatHandler

BIBTEX_CONTENT = """
@article{ref1,
  title = {First},
  author = {Doe, Jane},
}
@book{ref2,
  title = {Second},
}
"""


@pytest.mark.parametrize(
    ("handler_cls", "content", "expected_title"),
    [
        (BibTeXHandler, "@article{ref1,\n title = {First},\n}", "First"),
        (YamlHandler, "title: First\nauthor: Someone\n", "First"),
        (JsonHandler, '{"title": "First"}', "First"),
    ],
)
def test_match_and_lookup(
    handler_cls: type[ContentFormatHandler], content: str, expected_title: str
) -> None:
    evidence = LookupInput(kind="file", input="inline", content=content)
    instance = handler_cls.match_for_lookup(evidence)
    assert instance is not None

    result = instance.lookup(evidence)
    assert result.document is not None
    assert result.document["title"] == expected_title
    assert result.files == []


def test_parse_bibtex_content() -> None:
    parsed = BibTeXHandler.parse(BIBTEX_CONTENT)

    assert parsed is not None
    assert len(parsed.documents) == 2
    assert parsed.documents[0]["title"] == "First"
    assert parsed.documents[0]["type"] == "article"
    assert parsed.documents[1]["title"] == "Second"
    assert parsed.message is None


def test_parse_yaml_multiple_documents() -> None:
    content = "title: First\n---\ntitle: Second\n---\njust a scalar\n"
    parsed = YamlHandler.parse(content)

    assert parsed is not None
    assert parsed.documents == [{"title": "First"}, {"title": "Second"}]
    assert "1 non-dict" in (parsed.message or "")


def test_parse_yaml_single_document() -> None:
    parsed = YamlHandler.parse("title: The Title\nauthor: Someone\n")

    assert parsed is not None
    assert parsed.documents == [{"title": "The Title", "author": "Someone"}]
    assert parsed.message is None


def test_parse_json_object() -> None:
    parsed = JsonHandler.parse(json.dumps({"title": "The Title"}))

    assert parsed is not None
    assert parsed.documents == [{"title": "The Title"}]
    assert parsed.message is None


def test_parse_json_array() -> None:
    content = json.dumps([{"title": "First"}, 42, {"title": "Second"}])
    parsed = JsonHandler.parse(content)

    assert parsed is not None
    assert parsed.documents == [{"title": "First"}, {"title": "Second"}]
    # the drop is a diagnostic in the result, not a log line
    assert "1 non-object" in (parsed.message or "")


def test_parse_garbage_returns_none() -> None:
    # a parser failure is a decline (None), not an empty result
    assert JsonHandler.parse("hello world") is None


def test_parse_recognized_but_empty() -> None:
    # bibtex parses almost anything into zero documents: the format is
    # recognized, but there is no document to report
    parsed = BibTeXHandler.parse("hello world")
    assert parsed is not None
    assert parsed.documents == []


def test_lookup_multi_entry_message() -> None:
    """Both caveats (dropped elements and truncation) ride in one message,
    surfaced by the client instead of logged."""
    evidence = LookupInput(
        kind="file",
        input="inline",
        content='[{"title": "First"}, {"title": "Second"}, 42]',
    )
    instance = JsonHandler.match_for_lookup(evidence)
    assert instance is not None

    result = instance.lookup(evidence)

    assert result.document is not None
    assert result.document["title"] == "First"
    assert "1 non-object" in (result.message or "")
    assert "2 entries" in (result.message or "")


@pytest.mark.parametrize("handler_cls", [BibTeXHandler, YamlHandler, JsonHandler])
def test_match_garbage(handler_cls: type[SourceHandler]) -> None:
    garbage = LookupInput(kind="file", input="x", content="hello world")
    assert handler_cls.match_for_lookup(garbage) is None
    assert handler_cls.match_for_lookup(LookupInput(input="hello world")) is None


@pytest.mark.parametrize(
    ("handler_cls", "content"),
    [
        (BibTeXHandler, "@article{ref1,\n title = {First},\n}"),
        (YamlHandler, "title: First\n"),
    ],
)
def test_match_input_fallback(
    handler_cls: type[ContentFormatHandler], content: str
) -> None:
    evidence = LookupInput(input=content)
    instance = handler_cls.match_for_lookup(evidence)
    assert instance is not None

    result = instance.lookup(evidence)
    assert result.document is not None


def test_match_content_wins_over_input() -> None:
    # `input` is a fallback: when `content` parses, the path-like string in
    # `input` is never offered to the parser
    evidence = LookupInput(
        kind="file", input="title: From Input", content="title: From Content"
    )

    instance = YamlHandler.match_for_lookup(evidence)
    assert instance is not None
    assert instance.lookup(evidence).document == {"title": "From Content"}


@pytest.mark.parametrize(
    ("handler_cls", "content"),
    [
        (BibTeXHandler, "@article{ref1, title = {First}}"),
        (JsonHandler, '{"title": "First"}'),
        (YamlHandler, "title: First\n"),
    ],
)
def test_page_content_is_not_parsed(
    handler_cls: type[ContentFormatHandler], content: str
) -> None:
    """A web page may merely embed metadata (e.g. a citation example), so its
    content is never offered to a format parser."""
    page = LookupInput(input="https://x.org/article", kind="webpage", content=content)
    assert handler_cls.match_for_lookup(page) is None

    metadata_file = LookupInput(input="/tmp/refs", kind="file", content=content)
    assert handler_cls.match_for_lookup(metadata_file) is not None
