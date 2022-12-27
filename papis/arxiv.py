"""The following table lists the field prefixes for all the fields
 that can be searched.

 Table:          search_query field prefixes
============================================
 prefix          explanation
--------------------------------------------
 ti              Title
 au              Author
 abs             Abstract
 co              Comment
 jr              Journal Reference
 cat             Subject Category
 rn              Report Number
 id              Id (use id_list instead)
 all             All of the above
"""
import os
import re
import sys
from typing import Optional, List, Dict, Any

import click

import papis.config
import papis.downloaders.base
import papis.filetype
import papis.logging
import papis.utils

logger = papis.logging.get_logger(__name__)

ARXIV_API_URL = "https://arxiv.org/api/query"
ARXIV_ABS_URL = "https://arxiv.org/abs"
ARXIV_PDF_URL = "https://arxiv.org/pdf"


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
    dict_params = {
        "all": query,
        "ti": title,
        "au": author,
        "cat": category,
        "abs": abstract,
        "co": comment,
        "jr": journal,
        "id_list": id_list,
        "rn": report_number
    }
    result = []
    clean_params = {x: dict_params[x] for x in dict_params if dict_params[x]}
    search_query = "+AND+".join(
        ["{}:{}".format(key, clean_params[key]) for key in clean_params]
    )
    logger.debug("Performing query: '%s'.", search_query)

    with papis.utils.get_session() as session:
        response = session.get(
            ARXIV_API_URL,
            params={
                "search_query": search_query,
                "start": str(page),
                "max_results": str(max_results),
            })

    import bs4
    soup = bs4.BeautifulSoup(
        response.content,
        features="html.parser" if sys.version_info.minor < 6 else "lxml-xml")

    entries = soup.find_all("entry")
    for entry in entries:
        data = {}
        data["abstract"] = entry.find("summary").get_text().replace("\n", " ")
        data["url"] = entry.find("id").get_text()
        data["published"] = entry.find("published").get_text()
        published = data.get("published")
        if published:
            assert isinstance(published, str)
            data["year"] = published[0:4]
        data["title"] = entry.find("title").get_text().replace("\n", " ")
        data["author"] = ", ".join(
            [
                author.get_text().replace("\n", "")
                for author in entry.find_all("author")
            ]
        )
        result.append(data)
    return result


def validate_arxivid(arxivid: str) -> None:
    with papis.utils.get_session() as session:
        response = session.get("{}/{}".format(ARXIV_ABS_URL, arxivid))

    if not response.ok:
        raise ValueError(
            "HTTP ({} {}): '{}' not an arxivid".format(
                response.status_code, response.reason, arxivid)
            )


def pdf_to_arxivid(
        filepath: str,
        maxlines: float = float("inf"),      # noqa: B008
        ) -> Optional[str]:
    """Try to get arxivid from a filepath, it looks for a regex in the binary
    data and returns the first arxivid found, in the hopes that this arxivid
    is the correct one.

    :param filepath: Path to the pdf file
    :param maxlines: Maximum number of lines that should be checked
        For some documnets, it would spend a long time trying to look for
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
        r"(?P<arxivid>[^{fc}]+)"
        r'("|\'|\))?'
        .format(
            fc=forbidden_arxivid_characters
        ), re.I
    )
    miter = regex.finditer(text)

    from contextlib import suppress
    with suppress(StopIteration):
        m = next(miter)
        if m:
            return m.group("arxivid")

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
@click.option("--max", "-m", default=20, type=int)
def explorer(
        ctx: click.core.Context,
        query: str, author: str, title: str, abstract: str, comment: str,
        journal: str, report_number: str, category: str, id_list: str,
        page: int, max: int) -> None:
    """
    Look for documents on ArXiV.org.

    Examples of its usage are

        papis explore arxiv -a 'Hummel' -m 100 arxiv -a 'Garnet Chan' pick

    If you want to search for the exact author name 'John Smith', you should
    enclose it in extra quotes, as in the example below

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
        max_results=max)
    docs = [papis.document.from_data(data=d) for d in data]
    ctx.obj["documents"] += docs

    logger.info("Found %s documents.", len(docs))


class Downloader(papis.downloaders.Downloader):

    def __init__(self, url: str) -> None:
        super().__init__(uri=url, name="arxiv", expected_document_extension="pdf")
        self._arxivid = None  # type: Optional[str]

    @classmethod
    def match(cls, url: str) -> Optional[papis.downloaders.Downloader]:
        arxivid = find_arxivid_in_text(url)
        if arxivid:
            url = "{}/{}".format(ARXIV_ABS_URL, arxivid)
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

    def download_bibtex(self) -> None:
        arxivid = self.arxivid
        if not arxivid:
            return None

        import arxiv2bib

        bibtex_cli = arxiv2bib.Cli([arxivid])
        bibtex_cli.run()
        self.bibtex_data = "".join(bibtex_cli.output).replace("\n", " ")

    def get_document_url(self) -> Optional[str]:
        arxivid = self.arxivid
        if not arxivid:
            return None

        pdf_url = "{}/{}.pdf".format(ARXIV_PDF_URL, arxivid)
        self.logger.debug("Using document URL: '%s'.", pdf_url)

        return pdf_url


class Importer(papis.importer.Importer):

    """Importer accepting an arXiv ID and downloading files and data"""

    def __init__(self, uri: str) -> None:
        try:
            validate_arxivid(uri)
            aid = uri       # type: Optional[str]
        except ValueError:
            aid = find_arxivid_in_text(uri)

        uri = "{}/{}".format(ARXIV_ABS_URL, aid)

        super().__init__(name="arxiv", uri=uri)
        self.downloader = Downloader(uri)
        self.downloader._arxivid = aid

    @classmethod
    def match(cls, uri: str) -> Optional[papis.importer.Importer]:
        arxivid = find_arxivid_in_text(uri)
        if arxivid:
            return Importer(uri="{}/{}".format(ARXIV_ABS_URL, arxivid))

        try:
            validate_arxivid(uri)
        except ValueError:
            return None
        else:
            return Importer(uri="{}/{}".format(ARXIV_ABS_URL, uri))

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
        self.arxivid = None  # type: Optional[str]

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
