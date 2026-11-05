from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from papis.exceptions import SourceError
from papis.sources.client import lookup_followups
from papis.sources.handler import (
    FileReference,
    Followup,
    LookupInput,
    LookupOutput,
    SourceHandler,
)
from papis.sources.lookup import LookupResult, lookup
from papis.testing import make_lookup_handler

if TYPE_CHECKING:
    from typing import Any

    from papis.sources.dispatch import Status


def _match_all_evidence() -> LookupInput:
    return LookupInput(input="match")


def _result(
    source: str = "fake",
    *,
    priority: int = 5,
    status: Status = "ok",
    document: dict[str, Any] | None = None,
    files: list[FileReference] | None = None,
    followup: Followup | None = None,
) -> LookupResult:
    return LookupResult(
        source=source,
        priority=priority,
        status=status,
        document=document,
        files=files or [],
        followup=followup,
    )


def test_results_are_in_precedence_order(handler_registry: Any) -> None:
    low = make_lookup_handler("fake-low", priority=5, document={"title": "low"})
    first = make_lookup_handler("fake-first", priority=5, document={"title": "first"})
    high = make_lookup_handler("fake-high", priority=10, document={"title": "high"})
    handler_registry(low, first, high)

    results = lookup(_match_all_evidence())
    # precedence order; ties keep the registration order
    assert [result.source for result in results] == [
        "fake-low",
        "fake-first",
        "fake-high",
    ]
    assert [result.document for result in results] == [
        {"title": "low"},
        {"title": "first"},
        {"title": "high"},
    ]
    assert all(result.status == "ok" for result in results)


def test_declines_are_reported(handler_registry: Any) -> None:
    """Every handler is asked and declines are reported (the pinned path is
    exercised by the tests that pass ``sources=``)."""
    handler_registry(
        make_lookup_handler("fake-1", match_result=False),
        make_lookup_handler("fake-2", document={"title": "T"}),
    )

    assert [(r.source, r.status) for r in lookup(_match_all_evidence())] == [
        ("fake-1", "no_match"),
        ("fake-2", "ok"),
    ]


@pytest.mark.parametrize(
    ("handler_kwargs", "status", "message"),
    [
        # a match failure is not a lookup failure: nothing was claimed (the
        # lookup failure mapping itself is pinned in 'test_dispatch.py')
        (
            {"match_exc": RuntimeError("boom")},
            "match_failed",
            "RuntimeError: boom",
        ),
        ({"lookup_exc": SourceError("outage")}, "failed", "outage"),
        ({}, "no_result", None),
        # a successful handler's caveat rides in the result
        ({"document": {"title": "T"}, "message": "caveat"}, "ok", "caveat"),
    ],
)
def test_statuses(
    handler_registry: Any,
    handler_kwargs: dict[str, Any],
    status: str,
    message: str | None,
) -> None:
    handler_registry(make_lookup_handler("fake", **handler_kwargs))

    (result,) = lookup(_match_all_evidence(), sources=["fake"])
    assert result.status == status
    assert result.message == message


def test_files_ride_the_result(handler_registry: Any) -> None:
    urls = ["https://example.com/a", "https://example.com/b"]
    handler_registry(
        make_lookup_handler(
            "fake",
            document={"title": "T"},
            files=[FileReference(url=url) for url in urls],
        )
    )

    (result,) = lookup(_match_all_evidence(), sources=["fake"])
    assert result.status == "ok"
    assert [file.url for file in result.files] == urls

    # handlers whose document arrives via a followup (nber, thesesfr)
    # return their file references without a document
    handler_registry(
        make_lookup_handler("fake", files=[FileReference(url="https://example.com/doc.pdf")])
    )

    (result,) = lookup(_match_all_evidence(), sources=["fake"])
    assert result.status == "ok"
    assert result.document is None
    assert result.files[0].url == "https://example.com/doc.pdf"


def test_followup_folds_into_its_result(
    handler_registry: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    import papis.gather

    fetched: list[str] = []

    def _fetch_metadata_content(url: str) -> str:
        fetched.append(url)
        return "content"

    monkeypatch.setattr(papis.gather, "fetch_metadata_content", _fetch_metadata_content)

    chain = Followup(url="https://example.com/chain", format="yaml", priority=1)
    followup = Followup(
        url="https://example.com/export.bib", format="bibtex", priority=10
    )
    pdf = FileReference(url="https://example.com/paper.pdf")

    class _BibtexFormat(SourceHandler):
        name = "bibtex"
        priority = 12

        @classmethod
        def match_for_lookup(cls, evidence: LookupInput) -> SourceHandler | None:
            # only the followup's downloaded content reaches this handler
            return cls() if evidence.content else None

        def lookup(  # ruff: ignore[no-self-use]
            self, evidence: LookupInput
        ) -> LookupOutput:
            return LookupOutput(
                document={"title": "From bibtex export"}, followup=chain
            )

    handler_registry(
        make_lookup_handler("aps", followup=followup, files=[pdf]), _BibtexFormat
    )

    completed = lookup_followups(lookup(_match_all_evidence()))
    assert fetched == [followup.url]

    (result,) = [r for r in completed if r.document is not None]
    # the folded record keeps the emitter's attribution; neither the format
    # handler's priority nor the followup's leaks into it
    assert result.source == "aps"
    assert result.priority == 5
    assert result.document is not None
    assert result.document["title"] == "From bibtex export"
    assert result.files == [pdf]
    # followups cannot chain further (structural depth <= 2): the emitted
    # followup is silently dropped
    assert result.followup is None


def test_followup_priority(
    handler_registry: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    import papis.gather

    monkeypatch.setattr(papis.gather, "fetch_metadata_content", lambda url: "content")

    # a tie is won by the followup, which stays in the origin's slot among
    # its siblings. The format handler's priority is deliberately the
    # opposite of what the followup asks for: only the followup's own
    # priority may decide the fold.
    handler_registry(
        make_lookup_handler("fake-format", priority=1, document={"title": "done"})
    )
    origin = _result(
        "id",
        priority=5,
        document={"title": "origin"},
        followup=Followup(
            url="https://example.com/export", format="fake-format", priority=5
        ),
    )
    web = _result("web", priority=10, document={"title": "web"})

    completed = lookup_followups([origin, web])
    assert [result.document for result in completed] == [
        {"title": "done"},
        {"title": "web"},
    ]
    assert [result.source for result in completed] == ["id", "web"]

    # a followup above the origin wins even when the format handler ranks
    # below the origin
    handler_registry(
        make_lookup_handler(
            "fake-format", priority=1, document={"title": "From export"}
        )
    )
    origin = _result(
        "id",
        priority=10,
        document={"title": "Scraped title"},
        followup=Followup(
            url="https://example.com/export", format="fake-format", priority=11
        ),
    )

    (result,) = lookup_followups([origin])
    assert result.document == {"title": "From export"}

    # a followup below the origin's priority only fills gaps, even when the
    # format handler ranks above the origin
    handler_registry(
        make_lookup_handler(
            "fake-format",
            priority=20,
            document={"title": "From export", "year": "2024"},
        )
    )
    origin = _result(
        "id",
        priority=10,
        document={"title": "Scraped title"},
        followup=Followup(
            url="https://example.com/export", format="fake-format", priority=9
        ),
    )

    (result,) = lookup_followups([origin])
    assert result.document == {"title": "Scraped title", "year": "2024"}


@pytest.mark.parametrize(
    ("document", "exc_type", "status"),
    [
        (None, ConnectionError, "failed"),
        ({"title": "Scraped title"}, ConnectionError, "ok"),
        (None, RuntimeError, "failed"),
    ],
)
def test_followup_download_failure(
    monkeypatch: pytest.MonkeyPatch,
    document: dict[str, Any] | None,
    exc_type: type[Exception],
    status: str,
) -> None:
    """A failed followup download annotates a result that already has a
    document, and turns a document-less one into a failure."""
    import papis.utils

    def _fail_session() -> None:
        raise exc_type("network down")

    monkeypatch.setattr(papis.utils, "get_session", _fail_session)

    origin = _result(
        "aps",
        document=document,
        followup=Followup(
            url="https://example.com/export.bib", format="bibtex", priority=10
        ),
    )

    (result,) = lookup_followups([origin])
    assert result.status == status
    assert result.document == document
    assert result.followup is None
    assert "Could not fetch followup" in (result.message or "")


def test_followup_unknown_format(
    handler_registry: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A followup format must name a registered handler.

    A handler asking for an unknown format is a programming error, not bad
    data: it is reported loudly instead of silently degrading the request.
    """
    import papis.gather

    # the download has to succeed for the format to be resolved at all
    monkeypatch.setattr(papis.gather, "fetch_metadata_content", lambda url: "content")
    handler_registry()
    origin = _result(
        "aps",
        followup=Followup(
            url="https://example.com/export.bib", format="nope", priority=10
        ),
    )

    with pytest.raises(ValueError, match="unknown source 'nope'"):
        lookup_followups([origin])


def test_followup_failure_keeps_origin_document(
    handler_registry: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A failed followup lookup leaves the origin's document and files in
    place and only adds a caveat."""
    import papis.gather

    monkeypatch.setattr(papis.gather, "fetch_metadata_content", lambda url: "content")
    handler_registry(make_lookup_handler("fake-format", lookup_exc=SourceError("boom")))

    pdf = FileReference(url="https://example.com/paper.pdf")
    origin = _result(
        "aps",
        document={"title": "Scraped title"},
        files=[pdf],
        followup=Followup(
            url="https://example.com/export.bib", format="fake-format", priority=11
        ),
    )

    (result,) = lookup_followups([origin])
    assert result.status == "ok"
    assert result.document == {"title": "Scraped title"}
    assert result.files == [pdf]
    assert "boom" in (result.message or "")
    assert result.followup is None


@pytest.mark.parametrize(
    ("handler_kwargs", "status", "n_files"),
    [
        # the followup parsed no document
        ({}, "no_result", 1),
        # ... or only file references (appended after the origin's)
        (
            {"files": [FileReference(url="https://example.com/supp.pdf")]},
            "no_result",
            2,
        ),
        # the followup lookup failed
        ({"lookup_exc": SourceError("boom")}, "failed", 1),
        # the content was not the declared format
        ({"match_result": False}, "failed", 1),
    ],
)
def test_followup_decides_status_without_document(
    handler_registry: Any,
    monkeypatch: pytest.MonkeyPatch,
    handler_kwargs: dict[str, Any],
    status: str,
    n_files: int,
) -> None:
    """Without an origin document the followup's outcome decides the status,
    even when the origin carries file references."""
    import papis.gather

    monkeypatch.setattr(papis.gather, "fetch_metadata_content", lambda url: "content")
    handler_registry(make_lookup_handler("fake-format", **handler_kwargs))

    pdf = FileReference(url="https://example.com/paper.pdf")
    origin = _result(
        "id",
        priority=10,
        files=[pdf],
        followup=Followup(
            url="https://example.com/export", format="fake-format", priority=11
        ),
    )

    (result,) = lookup_followups([origin])
    assert result.status == status
    assert result.files[0] == pdf
    assert len(result.files) == n_files


def test_none_output_is_not_a_decline(handler_registry: Any) -> None:
    """``lookup`` returns an output, so ``None`` is a broken contract, not a
    decline: only ``parse`` declares an optional return and maps it to
    ``no_match``."""
    handler_registry(make_lookup_handler("broken", returns_none=True))

    (result,) = lookup(_match_all_evidence(), sources=["broken"])
    assert result.status == "failed"
    assert result.message is None


def test_failures_are_isolated(handler_registry: Any) -> None:
    """A match failure, a lookup failure and a success in one request: no
    handler's outcome suppresses another's."""
    handler_registry(
        make_lookup_handler("fake-match-fail", match_exc=RuntimeError("boom")),
        make_lookup_handler("fake-lookup-fail", lookup_exc=SourceError("down")),
        make_lookup_handler("fake-work", document={"title": "T"}),
    )

    results = lookup(LookupInput(input="1"))
    assert [(r.source, r.status) for r in results] == [
        ("fake-match-fail", "match_failed"),
        ("fake-lookup-fail", "failed"),
        ("fake-work", "ok"),
    ]


def test_empty_evidence_raises(handler_registry: Any) -> None:
    """Empty requests are rejected at the boundary; the offending request
    reaches no handler."""
    handler_registry(make_lookup_handler("fake"))

    with pytest.raises(ValueError, match="input string, content, or metadata fields"):
        lookup(LookupInput())


def test_fields_only_evidence_is_valid(handler_registry: Any) -> None:
    """Enrichment requests (``update --auto``) carry only fields; they are
    not empty evidence."""
    handler_registry(make_lookup_handler("fake", document={"title": "T"}))

    results = lookup(LookupInput(fields={"doi": "10.1234/x"}))
    assert results[0].status == "ok"


@pytest.mark.parametrize(
    ("evidence", "expected"),
    [
        # a local file contributes its name: the directory is not an identifier
        (LookupInput(input="/papers/2023/foo.pdf", kind="file"), "foo"),
        # a URL keeps its path: identifiers legitimately live in it
        (
            LookupInput(input="https://example.com/10.1234/foo", kind="file"),
            "https://example.com/10.1234/foo",
        ),
        # typed text is not a path
        (LookupInput(input="papers/2023/foo"), "papers/2023/foo"),
    ],
)
def test_file_input_is_reduced_to_its_name(
    handler_registry: Any, evidence: LookupInput, expected: str
) -> None:
    """Source handlers must not read identifiers out of path components."""
    names: list[str] = []

    class RecorderHandler(SourceHandler):
        name = "recorder"

        @classmethod
        def match_for_lookup(cls, evidence: LookupInput) -> SourceHandler | None:
            names.append(evidence.input)
            return cls()

        def lookup(self, evidence: LookupInput) -> LookupOutput:  # ruff: ignore[no-self-use]
            return LookupOutput()

    handler_registry(RecorderHandler)

    lookup(evidence)
    assert names == [expected]
