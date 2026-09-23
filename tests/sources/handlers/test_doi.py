from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import papis.crossref
from papis.sources.handler import LookupInput
from papis.sources.handlers.doi import DoiHandler

if TYPE_CHECKING:
    from typing import Any

    from papis.testing import TemporaryConfiguration

DOI = "10.1103/physrevb.89.140501"
DOC_URL = "https://journals.aps.org/prb/pdf/10.1103/PhysRevB.89.140501"


@pytest.mark.parametrize(
    ("evidence", "expected"),
    [
        (LookupInput(input=DOI), DOI),
        # marker form, case-insensitive DOIs, and padded field values
        (LookupInput(input=f"doi:{DOI}"), DOI),
        (LookupInput(input=DOI.upper()), DOI),
        (LookupInput(input="", fields={"doi": f" {DOI} "}), DOI),
        (LookupInput(input=""), None),
        (LookupInput(input="hello world"), None),
        (LookupInput(input="https://doi.org/10.1103/physrevb.89.140501"), DOI),
        # DOIs embedded in publisher URLs (legacy doi downloader behavior)
        (
            LookupInput(
                input="https://journals.aps.org/prb/abstract/10.1103/physrevb.89.140501"
            ),
            DOI,
        ),
        # URL syntax bounds the identifier: a ``/doi/pdf/`` path prefix and
        # query/parameter syntax are not part of the DOI
        (
            LookupInput(input="https://dl.acm.org/doi/pdf/10.1145/3544548.3583159"),
            "10.1145/3544548.3583159",
        ),
        (
            LookupInput(
                input="https://aip.scitation.org/doi/10.1063/1.4873138?foo=bar"
            ),
            "10.1063/1.4873138",
        ),
        # the doi handler's extraction is the basic case (site handlers
        # amend it locally), so a suffix-shaped path segment is part of
        # the DOI
        (LookupInput(input="10.5555/some/pdf"), "10.5555/some/pdf"),
        # the matcher follows the URL representation without needing a
        # scheme: raw query syntax ends the identifier, percent-encoded
        # name characters stay part of it
        (LookupInput(input="10.5555/abc?x=1"), "10.5555/abc"),
        (LookupInput(input="10.1000/456%23789"), "10.1000/456%23789"),
        # a schemeless URL must not let the marker scan capture the ``/doi/``
        # path segment (``abs/``, ``full/``, ``pdf/``) as part of the DOI
        (
            LookupInput(input="dl.acm.org/doi/abs/10.1145/3544548.3583159"),
            "10.1145/3544548.3583159",
        ),
        # a percent-encoded prefix slash does not match the pattern; the
        # legacy marker scan normalizes it
        (LookupInput(input="https://doi.org/10.5555%2Fabc"), "10.5555/abc"),
        # a matched URL without a DOI-shaped path does not match
        (LookupInput(input="https://iopscience.iop.org/journal/1742-6596"), None),
        (LookupInput(input="", fields={"title": "A title"}), None),
    ],
)
def test_match(evidence: LookupInput, expected: str | None) -> None:
    instance = DoiHandler.match_for_lookup(evidence)
    if expected is None:
        assert instance is None
    else:
        assert instance is not None
        assert instance.doi == expected


def test_lookup(
    tmp_config: TemporaryConfiguration, monkeypatch: pytest.MonkeyPatch
) -> None:
    data = {"title": "A paper", "doc_url": DOC_URL}
    monkeypatch.setattr(papis.crossref, "doi_to_data", lambda doi: data)

    result = DoiHandler(doi=DOI).lookup(LookupInput(input=DOI))
    assert result.document == data
    assert len(result.files) == 1
    assert result.files[0].url == DOC_URL


def test_lookup_no_data(
    tmp_config: TemporaryConfiguration, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail(doi: str) -> dict[str, Any]:
        raise ValueError(f"no data for {doi}")

    monkeypatch.setattr(papis.crossref, "doi_to_data", fail)

    result = DoiHandler(doi=DOI).lookup(LookupInput(input=DOI))
    assert result.document is None
    assert result.files == []
