from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import papis.dblp
import papis.utils
from papis.sources.handler import LookupInput, SearchInput
from papis.sources.handlers.dblp import DblpHandler
from tests.sources.helpers import FakeSession

if TYPE_CHECKING:
    from typing import Any

    from papis.testing import TemporaryConfiguration

_BIBTEX = """
@article{one,
    title = {The First Title},
    author = {Somebody},
}

@article{two,
    title = {The Second Title},
    author = {Somebody Else},
}
"""


@pytest.mark.parametrize(
    ("input_str", "expected_key"),
    [
        ("books/sp/02/ST2002", "books/sp/02/ST2002"),
        ("conf/iccg/EncarnacaoAFFGM93", "conf/iccg/EncarnacaoAFFGM93"),
        # syntactically claimed; existence fails at lookup
        ("books/sp/02", "books/sp/02"),
        # record-page URLs normalize to the key (query/fragment tolerated)
        ("https://dblp.org/rec/books/sp/02/ST2002.html", "books/sp/02/ST2002"),
        ("https://dblp.org/rec/books/sp/02/ST2002.html?param=1", "books/sp/02/ST2002"),
        # not keys: too short, wrong domain, non-record pages, DOIs
        ("books/sp", None),
        ("hello world", None),
        ("", None),
        ("https://dblp.net/rec/books/sp/02/ST2002.html", None),
        ("https://dblp.org/rec/books/sp/02/ST2002.bib", None),
        ("https://dblp.org/db/conf/iccg/index.html", None),
        ("10.1093/mind/fzae065", None),
        ("https://doi.org/10.1093/mind/fzae065", None),
    ],
)
def test_match(input_str: str, expected_key: str | None) -> None:
    instance = DblpHandler.match_for_lookup(LookupInput(input=input_str))
    if expected_key is None:
        assert instance is None
    else:
        assert instance is not None
        assert instance.dblp_key == expected_key


def test_lookup(
    tmp_config: TemporaryConfiguration, monkeypatch: pytest.MonkeyPatch
) -> None:
    session = FakeSession(_BIBTEX)
    monkeypatch.setattr(papis.utils, "get_session", lambda: session)

    result = DblpHandler("series/sci/2023-1062").lookup(
        LookupInput(input="series/sci/2023-1062")
    )

    assert result.document is not None
    assert result.document["title"] == "The First Title"
    assert "entries" in (result.message or "")


def test_lookup_not_found(
    tmp_config: TemporaryConfiguration, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A 404 from this record endpoint is absence, not an error."""
    monkeypatch.setattr(
        papis.utils, "get_session", lambda: FakeSession(status_code=404)
    )

    result = DblpHandler("series/sci/2023-1062").lookup(
        LookupInput(input="series/sci/2023-1062")
    )
    assert result.document is None


@pytest.mark.parametrize(
    ("status_code", "content"),
    [
        # DBLP reports a missing record with 404; the anti-bot page and
        # other failures arrive as a 200 without BibTeX
        (500, ""),
        (200, ""),
        (200, "<html>blocked</html>"),
    ],
)
def test_lookup_failure(
    tmp_config: TemporaryConfiguration,
    monkeypatch: pytest.MonkeyPatch,
    status_code: int,
    content: str,
) -> None:
    from papis.exceptions import SourceError

    monkeypatch.setattr(
        papis.utils,
        "get_session",
        lambda: FakeSession(content, status_code=status_code),
    )

    with pytest.raises(SourceError, match="DBLP"):
        DblpHandler("series/sci/2023-1062").lookup(
            LookupInput(input="series/sci/2023-1062")
        )


def test_search(
    tmp_config: TemporaryConfiguration, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: dict[str, Any] = {}
    monkeypatch.setattr(
        papis.dblp,
        "get_data",
        lambda **kwargs: calls.update(kwargs) or [{"title": "T"}],
    )

    result = DblpHandler.search(SearchInput(input="database systems"), max_results=10)

    assert result.documents[0]["title"] == "T"
    assert calls["query"] == "database systems"
