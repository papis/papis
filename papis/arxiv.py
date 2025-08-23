"""
Table: search_query field prefixes
==================================

The following table lists the field prefixes for all the fields
that can be searched. See the details of query construction in the
`arXiv API docs
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

import re
from typing import TYPE_CHECKING, Any

import papis.config
import papis.logging

if TYPE_CHECKING:
    import arxiv

logger = papis.logging.get_logger(__name__)

ARXIV_API_URL = "https://arxiv.org/api/query"
ARXIV_ABS_URL = "https://arxiv.org/abs"
ARXIV_PDF_URL = "https://arxiv.org/pdf"

# NOTE: keys match attributes of arxiv.Result
#   https://lukasschwab.me/arxiv.py/index.html#Result.__init__

_k = papis.document.KeyConversionPair
key_conversion = [
    _k("authors", [{
        "key": "author_list",
        "action": lambda x: papis.document.split_authors_name([
            author.name for author in x
            ])
    }]),
    _k("doi", [{"key": "doi", "action": None}]),
    _k("entry_id", [{"key": "url", "action": None}]),
    _k("journal_ref", [{"key": "journal", "action": None}]),
    _k("pdf_url", [{
        "key": papis.config.getstring("doc-url-key-name"),
        "action": None
    }]),
    _k("published", [
        {"key": "year", "action": lambda x: x.year},
        {"key": "month", "action": lambda x: x.month}
    ]),
    _k("summary", [{"key": "abstract", "action": lambda x: x.replace("\n", " ")}]),
    _k("title", [{"key": "title", "action": None}]),
    ]


def arxiv_to_papis(result: "arxiv.Result") -> dict[str, Any]:
    data = papis.document.keyconversion_to_data(key_conversion, vars(result))

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
    from papis.utils import get_session

    with get_session() as session:
        response = session.get(f"{ARXIV_ABS_URL}/{arxivid}")

    if not response.ok:
        raise ValueError(
            f"HTTP ({response.status_code} {response.reason}): "
            f"'{arxivid}' not an arxivid")


def is_arxivid(arxivid: str) -> bool:
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
    """Try to get arxivid from a filepath, it looks for a regex in the binary
    data and returns the first arxivid found, in the hopes that this arxivid
    is the correct one.

    :param filepath: Path to the pdf file
    :param maxlines: Maximum number of lines that should be checked
        For some documents, it would spend a long time trying to look for
        a arxivid, and arxivids in the middle of documents don't tend to be the
        correct arxivid of the document.
    :returns: arxivid or None
    """
    with open(filepath, "rb") as fd:
        for j, line in enumerate(fd):
            arxivid = find_arxivid_in_text(
                line.decode("ascii", errors="ignore"))
            if arxivid:
                return arxivid
            if j > maxlines:
                return None
    return None


def find_arxivid_in_text(text: str) -> str | None:
    """
    Try to find a arxivid in a text
    """
    forbidden_arxivid_characters = r'"\(\)\s%!$^\'<>@,;:#?&'
    # Sometimes it is in the javascript defined
    regex = re.compile(
        r"arxiv(.org|.com)?"
        r"(/abs|/pdf)?"
        r"\s*(=|:|/|\()\s*"
        r"(\"|')?"
        fr"(?P<arxivid>[^{forbidden_arxivid_characters}]+)"
        r'("|\'|\))?', re.I
    )
    miter = regex.finditer(text)

    from contextlib import suppress
    with suppress(StopIteration):
        m = next(miter)
        if m:
            aid = m.group("arxivid")
            aid = aid[:-4] if aid.endswith(".pdf") else aid
            return aid

    return None
