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

import os
import re
from typing import Any, Dict, List, Optional, TYPE_CHECKING

import click

import papis.config
import papis.downloaders.base
import papis.filetype
import papis.logging
import papis.utils

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
        "key": str(papis.config.get("doc-url-key-name")),
        "action": None
    }]),
    _k("published", [
        {"key": "year", "action": lambda x: x.year},
        {"key": "month", "action": lambda x: x.month}
    ]),
    _k("summary", [{"key": "abstract", "action": lambda x: x.replace("\n", " ")}]),
    _k("title", [{"key": "title", "action": None}]),
    ]


def arxiv_to_papis(result: "arxiv.Result") -> Dict[str, Any]:
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
        ) -> List[Dict[str, Any]]:
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
    except arxiv.arxiv.HTTPError:
        return []

    client = arxiv.Client()
    return [arxiv_to_papis(result) for result in client.results(search)]


def validate_arxivid(arxivid: str) -> None:
    with papis.utils.get_session() as session:
        response = session.get(f"{ARXIV_ABS_URL}/{arxivid}")

    if not response.ok:
        raise ValueError(
            f"HTTP ({response.status_code} {response.reason}): "
            f"'{arxivid}' not an arxivid")


def pdf_to_arxivid(
        filepath: str,
        maxlines: float = float("inf"),
        ) -> Optional[str]:
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


def find_arxivid_in_text(text: str) -> Optional[str]:
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


@click.command("arxiv")
@click.pass_context
@click.help_option("--help", "-h")
@click.option("--query", "-q", default="", type=str)
@click.option("--author", "-a", default="", type=str)
@click.option("--title", "-t", default="", type=str)
@click.option("--abstract", default="", type=str)
@click.option("--comment", default="", type=str)
@click.option("--journal", default="", type=str)
@click.option("--report-number", default="", type=str)
@click.option("--category", default="", type=str)
@click.option("--id-list", default="", type=str)
@click.option("--page", default=0, type=int)
@click.option("--max", "-m", "max_results", default=20, type=int)
def explorer(
        ctx: click.core.Context,
        query: str, author: str, title: str, abstract: str, comment: str,
        journal: str, report_number: str, category: str, id_list: str,
        page: int, max_results: int) -> None:
    """
    Look for documents on `arXiv.org <https://arxiv.org/>`__.


    For example, to search for documents with the authors "Hummer" and
    "Garnet Chan" (a maximum of 100 articles), use

    .. code:: sh

        papis explore arxiv -a 'Hummel' -m 100 arxiv -a 'Garnet Chan' pick

    If you want to search for the exact author name 'John Smith', you should
    enclose it in extra quotes, as in the example below

    .. code:: sh

        papis explore arxiv -a '"John Smith"' pick

    """
    logger.info("Looking up arXiv documents...")

    data = get_data(
        query=query,
        author=author,
        title=title,
        abstract=abstract,
        comment=comment,
        journal=journal,
        report_number=report_number,
        category=category,
        id_list=id_list,
        page=page or 0,
        max_results=max_results)
    docs = [papis.document.from_data(data=d) for d in data]
    ctx.obj["documents"] += docs

    logger.info("Found %s documents.", len(docs))


class Downloader(papis.downloaders.Downloader):
    """Retrieve documents from `arXiv <https://arxiv.org>`__"""

    def __init__(self, url: str) -> None:
        super().__init__(uri=url, name="arxiv", expected_document_extension="pdf")
        self._result: Optional[arxiv.Result] = None
        self._arxivid: Optional[str] = None

    @classmethod
    def match(cls, url: str) -> Optional[papis.downloaders.Downloader]:
        arxivid = find_arxivid_in_text(url)
        if arxivid:
            url = f"{ARXIV_ABS_URL}/{arxivid}"
            down = Downloader(url)
            down._arxivid = arxivid
            return down
        else:
            return None

    @property
    def arxivid(self) -> Optional[str]:
        if self._arxivid is None:
            self._arxivid = find_arxivid_in_text(self.uri)
            self.logger.debug("Found the arxivid '%s'.", self._arxivid)

        return self._arxivid

    @property
    def result(self) -> Optional["arxiv.Result"]:
        if self._result is None:
            import arxiv

            client = arxiv.Client()
            try:
                results = list(client.results(arxiv.Search(id_list=[self.arxivid])))
            except arxiv.arxiv.HTTPError:
                results = []

            if len(results) > 1:
                self.logger.error(
                    "Found multiple results for arxivid '%s'. Picking the first one!",
                    self.arxivid)

            if results:
                self._result = results[0]

        return self._result

    def get_data(self) -> Dict[str, Any]:
        result = self.result
        if result is None:
            return {}

        return arxiv_to_papis(self.result)

    def get_document_url(self) -> Optional[str]:
        result = self.result
        if result is None:
            return None

        self.logger.debug("pdf_url = '%s'", result.pdf_url)
        return str(result.pdf_url)


class Importer(papis.importer.Importer):

    """Importer accepting an arXiv ID and downloading files and data"""

    def __init__(self, uri: str) -> None:
        try:
            validate_arxivid(uri)
            aid: Optional[str] = uri
        except ValueError:
            aid = find_arxivid_in_text(uri)

        uri = f"{ARXIV_ABS_URL}/{aid}"

        super().__init__(name="arxiv", uri=uri)
        self.downloader = Downloader(uri)
        self.downloader._arxivid = aid

    @classmethod
    def match(cls, uri: str) -> Optional[papis.importer.Importer]:
        arxivid = find_arxivid_in_text(uri)
        if arxivid:
            return Importer(uri=f"{ARXIV_ABS_URL}/{arxivid}")

        try:
            validate_arxivid(uri)
        except ValueError:
            return None
        else:
            return Importer(uri=f"{ARXIV_ABS_URL}/{uri}")

    @property
    def arxivid(self) -> Optional[str]:
        return self.downloader.arxivid

    def fetch_data(self) -> None:
        self.downloader.fetch_data()
        self.ctx.data = self.downloader.ctx.data.copy()

    def fetch_files(self) -> None:
        self.downloader.fetch_files()
        self.ctx.files = self.downloader.ctx.files.copy()


class ArxividFromPdfImporter(papis.importer.Importer):

    """Importer parsing an arXiv ID from a PDF file"""

    def __init__(self, uri: str) -> None:
        super().__init__(name="pdf2arxivid", uri=uri)
        self.arxivid: Optional[str] = None

    @classmethod
    def match(cls, uri: str) -> Optional[papis.importer.Importer]:
        if (os.path.isdir(uri) or not os.path.exists(uri)
                or not papis.filetype.get_document_extension(uri) == "pdf"):
            return None
        importer = ArxividFromPdfImporter(uri=uri)
        importer.arxivid = pdf_to_arxivid(uri, maxlines=2000)
        return importer if importer.arxivid else None

    def fetch(self) -> None:
        self.logger.info("Trying to parse arxivid from file '%s'.", self.uri)
        if not self.arxivid:
            self.arxivid = pdf_to_arxivid(self.uri, maxlines=2000)

        if self.arxivid:
            self.logger.info("Parsed arxivid '%s'.", self.arxivid)
            self.logger.warning(
                "There is no guarantee that this arxivid is the correct one!")

            importer = Importer.match(self.arxivid)
            if importer:
                importer.fetch()
                self.ctx = importer.ctx
        else:
            self.logger.info("No arxivid found in file: '%s'.", self.uri)
