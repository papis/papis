"""
Table: search_query field prefixes
==================================

The following table lists the field prefixes for all the fields that can be
searched. See the details of query construction in the `arXiv API docs
<https://info.arxiv.org/help/api/user-manual.html#51-details-of-query-construction>`__.

====== ========================
Prefix Explanation
====== ========================
ti     Title
au     Author
abs    Abstract
co     Comment
jr     Journal Reference
cat    Subject Category
rn     Report Number
id     Id (use id_list instead)
all    All of the above
====== ========================
"""
from __future__ import annotations

import os
import re
from functools import cache
from typing import TYPE_CHECKING, Any

import papis.config
import papis.logging
from papis.exceptions import SourceError

if TYPE_CHECKING:
    from collections.abc import Sequence

    import arxiv

    from papis.document import KeyConversionPair

logger = papis.logging.get_logger(__name__)


@cache
def _get_arxiv_key_conversions() -> list[KeyConversionPair]:
    # NOTE: keys match attributes of arxiv.Result
    #   https://lukasschwab.me/arxiv.py/index.html#Result.__init__

    from papis.document import KeyConversionPair, split_authors_name

    return [
        KeyConversionPair("authors", [{
            "key": "author_list",
            "action": lambda x: split_authors_name([author.name for author in x])
        }]),
        KeyConversionPair("doi", [{"key": "doi", "action": None}]),
        KeyConversionPair("entry_id", [{"key": "url", "action": None}]),
        KeyConversionPair("journal_ref", [{"key": "journal", "action": None}]),
        KeyConversionPair("pdf_url", [{
            "key": papis.config.getstring("doc-url-key-name"),
            "action": None
        }]),
        KeyConversionPair("published", [
            {"key": "year", "action": lambda x: x.year},
            {"key": "month", "action": lambda x: x.month}
        ]),
        KeyConversionPair("summary", [
            {"key": "abstract", "action": lambda x: x.replace("\n", " ")},
        ]),
        KeyConversionPair("title", [{"key": "title", "action": None}]),
    ]


def arxiv_to_papis(result: arxiv.Result) -> dict[str, Any]:
    from papis.document import keyconversion_to_data

    key_conversion = _get_arxiv_key_conversions()
    data = keyconversion_to_data(key_conversion, vars(result))

    # NOTE: these tags are recognized by BibLaTeX
    data["eprint"] = result.get_short_id()
    data["eprinttype"] = "arxiv"
    data["eprintclass"] = result.primary_category

    # NOTE: not quite sure what to do about the type? it's not mentioned explicitly
    data["type"] = "article"
    if result.comment is not None:
        comment = result.comment.lower()
        if "thesis" in comment:
            if "phd" in comment:
                data["type"] = "phdthesis"
            elif "master" in comment:
                data["type"] = "mastersthesis"
            else:
                data["type"] = "thesis"

    return data


def _query_term(name: str, value: str | Sequence[str]) -> str:
    """Build a query term for *name* from *value*."""
    values = [value] if isinstance(value, str) else value
    terms = []
    for item in values:
        # NOTE: the query language has no escape for a quote inside a phrase, so drop
        # them (and collapse whitespace) instead of breaking the query.
        # See <https://info.arxiv.org/help/api/user-manual.html#51-details-of-query-construction>.
        text = " ".join(item.replace('"', " ").split())
        if not text:
            continue

        if " " in text or "(" in text or ")" in text:
            terms.append(f'{name}:"{text}"')
        else:
            terms.append(f"{name}:{text}")

    if len(terms) > 1:
        return f"({' OR '.join(terms)})"

    return terms[0] if terms else ""


def get_data(
        query: str = "",
        author: str | Sequence[str] = "",
        title: str | Sequence[str] = "",
        abstract: str | Sequence[str] = "",
        comment: str | Sequence[str] = "",
        journal: str | Sequence[str] = "",
        report_number: str | Sequence[str] = "",
        category: str | Sequence[str] = "",
        id_list: str | Sequence[str] = "",
        max_results: int = 30
        ) -> list[dict[str, Any]]:
    """
    Retrieve data from arXiv based on the given query parameters.
    """
    # form query
    search_params = {
        "all": query,
        "ti": title,
        "au": author,
        "cat": category,
        "abs": abstract,
        "co": comment,
        "jr": journal,
        "rn": report_number
    }
    search_query = " AND ".join(
        [term for term in (_query_term(key, value)
                           for key, value in search_params.items()) if term]
    )
    logger.debug("Performing query: '%s'.", search_query)

    # gather results
    import arxiv

    ids = [id_list] if isinstance(id_list, str) else list(id_list)
    search = arxiv.Search(
        query=search_query,
        max_results=max_results,
        id_list=ids,
        )

    from requests.exceptions import RequestException

    try:
        client = arxiv.Client()
        return [arxiv_to_papis(result) for result in client.results(search)]
    except (arxiv.ArxivError, RequestException) as exc:
        raise SourceError(f"Could not query arXiv: {exc}") from exc


def pdf_to_arxivid(
        filepath: str,
        maxlines: float = float("inf"),
        ) -> str | None:
    """
    Find an arXiv identifier in the given *filepath*.

    This function uses a simple regular expression to look through the data in
    the given file (usually a PDF file) for an arXiv identifier. It uses
    :func:`find_arxivid_in_text` to perform the check on each line of text.

    In practice, it is recommended to set *maxlines* to a reasonable value,
    e.g. 1000 lines. Most documents downloaded from arXiv have the required
    identifier on the first page, so performing a longer search is suboptimal.
    Furthermore, if an arXiv identifier is found further away from the first
    page, it is more likely to not correspond to the current document.

    :param filepath: a path to an existing file.
    :param maxlines: maximum number of lines that should be checked.
    :returns: an arXiv identifier, if any could be found, or *None* otherwise.
    """
    if not os.path.exists(filepath):
        return None

    with open(filepath, "rb") as fd:
        for j, line in enumerate(fd):
            arxivid = find_arxivid_in_text(
                line.decode("ascii", errors="ignore"))

            if arxivid:
                return arxivid

            if j > maxlines:
                return None

    return None


# NOTE: identifiers may be defined in javascript, hence the broad set of separators and
# the optional quotes. Matching new style (``1701.08223v2``) or old style
# (``hep-th/9901001``).
_ARXIVID_CORE = (
    r"(?:\d{4}\.\d{4,5}(?:v\d+)?|[a-z-]+(?:\.[A-Za-z-]+)?/\d{7}(?:v\d+)?)"
)

_ARXIVID_REGEX = re.compile(
    r"arxiv(?:\.org|\.com)?"
    r"(?:/abs|/pdf)?"
    r"\s*(?:=|:|/|\()\s*"
    r"[\"']?"
    fr"(?P<arxivid>{_ARXIVID_CORE})"
    r"(?!\d)"
    r"[\"'\)]?",
    re.I
)

# NOTE: a bare identifier must be the whole input (minus surrounding white space)
_ARXIVID_BARE_REGEX = re.compile(rf"\A\s*({_ARXIVID_CORE})\s*\Z", re.I)


def find_arxivid_in_text(text: str) -> str | None:
    """
    Find an arXiv identifier in the given *text*.

    Two forms are recognized: an identifier introduced by an ``arxiv`` marker (URLs,
    ``arXiv:`` prefixes, javascript assignments, ...), which may be located anywhere in
    the text, and a bare identifier that forms the whole input.

    :returns: an arXiv identifier, if any could be found, or *None* otherwise.
    """
    match = _ARXIVID_REGEX.search(text)
    if match:
        return match.group("arxivid")

    match = _ARXIVID_BARE_REGEX.match(text)
    return match.group(1) if match else None
