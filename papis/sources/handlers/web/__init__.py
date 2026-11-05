"""Web source handlers."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, ClassVar, TypedDict

import papis.config
from papis.exceptions import SourceError
from papis.sources.handler import (
    FileReference,
    Followup,
    LookupOutput,
    SourceHandler,
)

if TYPE_CHECKING:
    from collections.abc import Iterator

    from bs4 import BeautifulSoup

    from papis.sources.handler import LookupInput


class MetaEquivalence(TypedDict):
    tag: str
    key: str
    attrs: dict[str, str | re.Pattern[str]]


meta_equivalences: list[MetaEquivalence] = [
    # google
    {"tag": "meta", "key": "abstract", "attrs": {"name": "description"}},
    {"tag": "meta", "key": "doi", "attrs": {"name": "doi"}},
    {"tag": "meta", "key": "keywords", "attrs": {"name": "keywords"}},
    {"tag": "title", "key": "title", "attrs": {}},
    # facebook
    {"tag": "meta", "key": "type", "attrs": {"property": "og:type"}},
    {"tag": "meta", "key": "abstract", "attrs": {"property": "og:description"}},
    {"tag": "meta", "key": "title", "attrs": {"property": "og:title"}},
    {"tag": "meta", "key": "url", "attrs": {"property": "og:url"}},
    # citation style
    # https://scholar.google.com/intl/en/scholar/inclusion.html#indexing
    {"tag": "meta", "key": "doi", "attrs": {"name": "citation_doi"}},
    {"tag": "meta", "key": "firstpage", "attrs": {"name": "citation_firstpage"}},
    {"tag": "meta", "key": "lastpage", "attrs": {"name": "citation_lastpage"}},
    {"tag": "meta", "key": "url", "attrs": {"name": "citation_fulltext_html_url"}},
    {"tag": "meta", "key": "pdf_url", "attrs": {"name": "citation_pdf_url"}},
    {"tag": "meta", "key": "issn", "attrs": {"name": "citation_issn"}},
    {"tag": "meta", "key": "issue", "attrs": {"name": "citation_issue"}},
    {"tag": "meta", "key": "abstract", "attrs": {"name": "citation_abstract"}},
    {
        "tag": "meta",
        "key": "journal_abbrev",
        "attrs": {"name": "citation_journal_abbrev"},
    },
    {"tag": "meta", "key": "journal", "attrs": {"name": "citation_journal_title"}},
    {"tag": "meta", "key": "language", "attrs": {"name": "citation_language"}},
    {"tag": "meta", "key": "online_date", "attrs": {"name": "citation_online_date"}},
    {
        "tag": "meta",
        "key": "publication_date",
        "attrs": {"name": "citation_publication_date"},
    },
    {"tag": "meta", "key": "publisher", "attrs": {"name": "citation_publisher"}},
    {"tag": "meta", "key": "title", "attrs": {"name": "citation_title"}},
    {"tag": "meta", "key": "volume", "attrs": {"name": "citation_volume"}},
    # dc.{id} style
    {
        "tag": "meta",
        "key": "publisher",
        "attrs": {"name": re.compile(r"dc.publisher", re.I)},
    },
    {
        "tag": "meta",
        "key": "publisher",
        "attrs": {"name": re.compile(r".*st.publisher.*", re.I)},
    },
    {"tag": "meta", "key": "date", "attrs": {"name": re.compile(r"dc.date", re.I)}},
    {
        "tag": "meta",
        "key": "language",
        "attrs": {"name": re.compile(r"dc.language", re.I)},
    },
    {
        "tag": "meta",
        "key": "issue",
        "attrs": {"name": re.compile(r"dc.citation.issue", re.I)},
    },
    {
        "tag": "meta",
        "key": "volume",
        "attrs": {"name": re.compile(r"dc.citation.volume", re.I)},
    },
    {
        "tag": "meta",
        "key": "keywords",
        "attrs": {"name": re.compile(r"dc.subject", re.I)},
    },
    {"tag": "meta", "key": "title", "attrs": {"name": re.compile(r"dc.title", re.I)}},
    {"tag": "meta", "key": "type", "attrs": {"name": re.compile(r"dc.type", re.I)}},
    {
        "tag": "meta",
        "key": "abstract",
        "attrs": {"name": re.compile(r"dc.description", re.I)},
    },
    {
        "tag": "meta",
        "key": "abstract",
        "attrs": {"name": re.compile(r"dc.description.abstract", re.I)},
    },
    {
        "tag": "meta",
        "key": "journal_abbrev",
        "attrs": {"name": re.compile(r"dc.relation.ispartof", re.I)},
    },
    {"tag": "meta", "key": "year", "attrs": {"name": re.compile(r"dc.issued", re.I)}},
    {
        "tag": "meta",
        "key": "doi",
        "attrs": {"name": re.compile(r"dc.identifier", re.I), "scheme": "doi"},
    },
]


def parse_meta_authors(soup: BeautifulSoup) -> list[dict[str, Any]]:
    """Extract the author list with affiliations when given."""
    # find author tags
    authors = soup.find_all(name="meta", attrs={"name": "citation_author"})
    if not authors:
        authors = soup.find_all(
            name="meta", attrs={"name": re.compile(r"dc.creator", re.I)}
        )

    if not authors:
        return []

    # find affiliation tags
    affs = soup.find_all(name="meta", attrs={"name": "citation_author_institution"})

    if affs and len(authors) == len(affs):
        authors_and_affs: Iterator[tuple[Any, Any]] = zip(authors, affs, strict=True)
    else:
        authors_and_affs = ((a, None) for a in authors)

    from papis.document import split_author_name

    # convert to papis author format
    author_list: list[dict[str, Any]] = []
    for author, aff in authors_and_affs:
        fullname = split_author_name(author.get("content"))
        affiliation = [{"name": aff.get("content")}] if aff else []

        author_list.append({
            "given": fullname["given"],
            "family": fullname["family"],
            "affiliation": affiliation,
        })

    return author_list


def parse_meta_headers(soup: BeautifulSoup) -> dict[str, Any]:
    """Extract simple metadata fields."""
    data: dict[str, Any] = {}
    for equiv in meta_equivalences:
        elements = soup.find_all(equiv["tag"], attrs=equiv["attrs"])
        if not elements:
            continue

        element = elements[0]
        if equiv["tag"] == "title":
            value = element.text.strip()
        else:
            content = element.attrs.get("content")
            value = str(content).replace("\r", "") if content is not None else ""

        if value:
            data[equiv["key"]] = value

    from papis.document import author_list_to_author

    # ensure that author and author_list are in sync
    author_list = parse_meta_authors(soup)
    if author_list:
        data["author_list"] = author_list
        data["author"] = author_list_to_author(data)

    # convert firstpage / lastpage to pages
    firstpage = data.get("firstpage")
    if firstpage:
        lastpage = data.get("lastpage")
        if lastpage:
            data["pages"] = f"{firstpage}--{lastpage}"
        else:
            data["pages"] = firstpage

    from papis.bibtex import bibtex_type_converter

    # ensure we use a standard BibTeX type
    bib_type = data.get("type")
    if bib_type in bibtex_type_converter:
        data["type"] = bibtex_type_converter[bib_type]

    pdf_url = data.pop("pdf_url", None)
    if pdf_url is not None:
        data[papis.config.getstring("doc-url-key-name")] = pdf_url

    return data


class WebsiteHandler(SourceHandler):
    """Base class for handlers that scrape metadata from a website's page.

    The page is fetched by the client during gathering, and the handler only ever works
    on ``evidence.content``. Handlers may set :attr:`enrich_from_doi` to get more
    metadata via a DOI. Some subclasses emit :class:`Followup` with an URL to a BibTeX
    file to be downloaded for additional metadata.
    """

    priority: ClassVar[int] = 10

    #: the default :meth:`get_page_url_or_id` gets inputs matching this regex.
    url_or_id_re: ClassVar[re.Pattern[str]]

    #: expected extension of the file from :meth:`get_file_url`.
    file_extension: ClassVar[str | None] = "pdf"

    #: whether the DOI is used to find metadata.
    enrich_from_doi: ClassVar[bool] = False

    def __init__(self, url: str) -> None:
        super().__init__()
        self.url = url

    @classmethod
    def match_for_lookup(cls, evidence: LookupInput) -> WebsiteHandler | None:
        if evidence.kind == "file":
            return None

        url_or_id = cls.get_page_url_or_id(evidence.input)
        return cls(url_or_id) if url_or_id is not None else None

    def lookup(self, evidence: LookupInput) -> LookupOutput:
        self.data = self.scrape(evidence)

        message = None
        doi = self.data.get("doi") or self.get_doi(evidence)
        if doi:
            self.data["doi"] = doi

            if self.enrich_from_doi:
                from papis.sources.handlers.doi import DoiHandler

                try:
                    doi_data = DoiHandler(doi).lookup(evidence).document
                except SourceError as exc:
                    self.logger.debug(
                        "Could not retrieve data for DOI '%s'.",
                        doi,
                        exc_info=exc,
                    )
                    doi_data = None

                if doi_data:
                    self.data = {**doi_data, **self.data}
                else:
                    message = f"Could not retrieve additional metadata for DOI '{doi}'."

        file_url = self.get_file_url(evidence)
        bibtex_url = self.get_bibtex_url(evidence)

        document = self.data if self.data else None

        files: list[FileReference] = []
        if file_url is not None:
            files = [FileReference(url=file_url, extension=self.file_extension)]

        followup = None
        if bibtex_url is not None:
            followup = Followup(
                url=bibtex_url,
                format="bibtex",
                priority=self.priority + 1,
            )

        return LookupOutput(
            document=document,
            files=files,
            followup=followup,
            message=message,
        )

    @classmethod
    def get_page_url_or_id(cls, input: str) -> str | None:
        """Return the page URL or bare identifier for *input*, else ``None``."""
        return input if cls.url_or_id_re.search(input) else None

    def _get_soup(self, content: str) -> Any:  # ruff: ignore[no-self-use]
        """Parse the page *content* into a BeautifulSoup object."""
        import bs4

        return bs4.BeautifulSoup(content, features="lxml")

    def get_doi(self, evidence: LookupInput) -> str | None:  # ruff: ignore[no-self-use]
        """Return the DOI for the current page, else ``None``."""
        return None

    def scrape(self, evidence: LookupInput) -> dict[str, Any]:
        """Scrape the page into document data."""
        if evidence.content is None:
            return {}

        return parse_meta_headers(self._get_soup(evidence.content))

    def get_file_url(self, evidence: LookupInput) -> str | None:
        """Derive the URL of the downloadable file (usually the PDF)."""
        doc_url = self.data.get(papis.config.getstring("doc-url-key-name"))
        return str(doc_url) if doc_url else None

    def get_bibtex_url(self, evidence: LookupInput) -> str | None:  # ruff: ignore[no-self-use]
        """Derive the BibTeX export URL from the page URL and/or scraped data."""
        return None


class FallbackHandler(WebsiteHandler):
    """Retrieve documents from arbitrary websites."""

    name = "fallback"
    priority: ClassVar[int] = 1
    url_or_id_re = re.compile(r"^https?://", re.IGNORECASE)
    file_extension = None

    def scrape(self, evidence: LookupInput) -> dict[str, Any]:
        data = super().scrape(evidence)

        if data and "url" not in data:
            data["url"] = evidence.input

        return data

    def get_doi(self, evidence: LookupInput) -> str | None:
        if evidence.content is None:
            return None

        from doi import find_doi_in_text

        return find_doi_in_text(str(self._get_soup(evidence.content)))


__all__ = ["FallbackHandler", "WebsiteHandler"]
