from __future__ import annotations

from functools import cache
from typing import TYPE_CHECKING, Any

from papis.exceptions import SourceError

if TYPE_CHECKING:
    from papis.document import KeyConversionPair

#: Name of the official PubMed database (see the `official documentation <
#: https://api.ncbi.nlm.nih.gov/lit/ctxp>`__).
PUBMED_DATABASE = "pubmed"
#: Query URL for PubMed metadata.
PUBMED_URL = "https://api.ncbi.nlm.nih.gov/lit/ctxp/v1/{database}/?format=csl&id={pmid}"

#: A mapping of additional document types supported by PubMed to their BibTeX
#: equivalents. These types are taken from the `official citation styles
#: <https://docs.citationstyles.org/en/stable/specification.html#appendix-iii-types>`__.
PUBMED_TO_BIBTEX_TYPE_CONVERT = {
    "article": "article",
    "article-journal": "article",
    "book": "book",
    "chapter": "inbook",
    "paper-conference": "inproceedings",
    "report": "report",
    "thesis": "phdthesis",
}


def _handle_pubmed_pages(pages: str) -> str:
    # returned data is in the form 561-7 meaning 562-567
    start, end = [x.strip() for x in pages.split("-")]
    prefix = start[:max(0, len(start) - len(end))]
    end = f"{prefix}{end}"

    return f"{start}--{end}"


@cache
def _get_pubmed_key_conversion() -> list[KeyConversionPair]:
    from papis.document import EmptyKeyConversion, KeyConversionPair

    return [
        KeyConversionPair("container-title", [{"key": "journal", "action": None}]),
        KeyConversionPair("PMID", [
            {"key": "pmid", "action": None},
            ]),
        KeyConversionPair("ISSN", [{"key": "issn", "action": None}]),
        KeyConversionPair("DOI", [{"key": "doi", "action": None}]),
        KeyConversionPair("page", [
            {"key": "pages", "action": _handle_pubmed_pages}
            ]),
        KeyConversionPair("type", [{
            "key": "type",
            "action": lambda x: PUBMED_TO_BIBTEX_TYPE_CONVERT.get(x, "misc")
            }]),
        KeyConversionPair("author", [{"key": "author_list", "action": None}]),
        KeyConversionPair("issued", [
            {"key": "year", "action": lambda x: x["date-parts"][0][0]},
            ]),
        KeyConversionPair("volume", [EmptyKeyConversion]),
        KeyConversionPair("issue", [EmptyKeyConversion]),
        KeyConversionPair("title", [EmptyKeyConversion]),
        KeyConversionPair("publisher", [EmptyKeyConversion]),
    ]


def pubmed_data_to_papis_data(data: dict[str, Any]) -> dict[str, Any]:
    from papis.document import author_list_to_author, keyconversion_to_data

    key_conversion = _get_pubmed_key_conversion()
    new_data = keyconversion_to_data(key_conversion, data)
    new_data["author"] = author_list_to_author(new_data)

    return new_data


def is_valid_pmid(pmid: str) -> bool:
    pmid = pmid.strip()
    if not pmid.isdigit():
        return False

    from papis.utils import get_session

    with get_session() as session:
        response = session.get(PUBMED_URL.format(pmid=pmid, database=PUBMED_DATABASE))

    return response.ok


def get_data(query: str = "") -> dict[str, Any]:
    import json

    from requests.exceptions import RequestException

    from papis import PAPIS_USER_AGENT
    from papis.utils import get_session

    # NOTE: being nice and using the project version as a user agent
    # as requested in https://api.ncbi.nlm.nih.gov/lit/ctxp
    try:
        with get_session() as session:
            response = session.get(
                PUBMED_URL.format(pmid=query.strip(), database=PUBMED_DATABASE),
                headers={"user-agent": PAPIS_USER_AGENT},
                )
    except RequestException as exc:
        raise SourceError(f"Could not query PubMed: {exc}") from exc

    if not response.ok:
        raise SourceError(
            f"Could not query PubMed: HTTP {response.status_code} ({response.reason})")

    try:
        data = json.loads(response.content.decode())
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise SourceError(f"Unexpected response from PubMed: {exc}") from exc

    if not data:
        return {}

    if not isinstance(data, dict):
        raise SourceError(
            f"Unexpected response from PubMed: expected a JSON object, "
            f"got '{type(data).__name__}'.")

    return pubmed_data_to_papis_data(data)
