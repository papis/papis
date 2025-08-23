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

import os
import re
from functools import cache
from typing import TYPE_CHECKING, Any

import papis.logging

if TYPE_CHECKING:
    import arxiv

    import papis.document

logger = papis.logging.get_logger(__name__)

#: Official arXiv API endpoint.
ARXIV_API_URL = "https://arxiv.org/api/query"
#: Base URL for arXiv article abstract pages.
ARXIV_ABS_URL = "https://arxiv.org/abs"
#: Base URL for arXiv article file pages.
ARXIV_PDF_URL = "https://arxiv.org/pdf"


@cache
def _get_arxiv_key_conversions() -> list["papis.document.KeyConversionPair"]:
    # NOTE: keys match attributes of arxiv.Result
    #   https://lukasschwab.me/arxiv.py/index.html#Result.__init__

    from papis.config import getstring
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
            "key": getstring("doc-url-key-name"),
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


def arxiv_to_papis(result: "arxiv.Result") -> dict[str, Any]:
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


def get_data(
        query: str = "",
        author: str = "",
        title: str = "",
        abstract: str = "",
        comment: str = "",
        journal: str = "",
        report_number: str = "",
        category: str = "",
        id_list: str = "",
        page: int = 0,
        max_results: int = 30
        ) -> list[dict[str, Any]]:
    """
    Retrieve data from arXiv based on the given query parameters.
    """
    from urllib.parse import quote

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
        [f"{key}:{quote(value)}" for key, value in search_params.items() if value]
    )
    logger.debug("Performing query: '%s'.", search_query)

    # gather results
    import arxiv

    try:
        search = arxiv.Search(
            query=search_query,
            max_results=max_results,
            id_list=id_list.split(";"),
            )
    except arxiv.ArxivError as exc:
        logger.error("Failed to download metadata from arXiv.", exc_info=exc)
        return []

    client = arxiv.Client()
    return [arxiv_to_papis(result) for result in client.results(search)]


def validate_arxivid(arxivid: str) -> None:
    """
    Check if the given arXiv identifier exists.

    This function tries to perform a web query for the identifier. If it is not
    found, a :exc:`ValueError` is raised.
    """
    from papis.utils import get_session

    with get_session() as session:
        response = session.get(f"{ARXIV_ABS_URL}/{arxivid}")

    if not response.ok:
        raise ValueError(
            f"HTTP ({response.status_code} {response.reason}): "
            f"'{arxivid}' not an arxivid")


def is_arxivid(arxivid: str) -> bool:
    """
    Check if a given arXiv identifier exists.

    This function uses :func:`validate_arxivid` to check the identifier, but is
    meant to be used in a boolean expression.
    """
    try:
        validate_arxivid(arxivid)
    except ValueError:
        return False
    else:
        return True


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


# NOTE: sometimes it is defined in javascript too, so this regex is very broad.
_ARXIVID_FORBIDDEB_CHARACTERS = r'"\(\)\s%!$^\'<>@,;:#?&'
_ARXIVID_REGEX = re.compile(
    r"arxiv(.org|.com)?"
    r"(/abs|/pdf)?"
    r"\s*(=|:|/|\()\s*"
    r"(\"|')?"
    fr"(?P<arxivid>[^{_ARXIVID_FORBIDDEB_CHARACTERS}]+)"
    r'("|\'|\))?',
    re.I
)


def find_arxivid_in_text(text: str) -> str | None:
    """
    Find an arXiv identifier in the given *text*.

    This function searches for the arXiv identifier using a simple regular
    expression. This regular expression is not exact, so there could be false
    positives. To ensure that the returned value is a valid arXiv identifier,
    use :func:`validate_arxivid` or :func:`is_arxivid`.

    :returns: an arXiv identifier, if any could be found, or *None* otherwise.
    """
    for match in _ARXIVID_REGEX.finditer(text):
        aid = match.group("arxivid")
        aid = aid[:-4] if aid.endswith(".pdf") else aid
        return aid

    return None
