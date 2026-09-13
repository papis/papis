from __future__ import annotations

import os
import tempfile
from typing import Any

from papis.importer import Importer

# Maximum number of file lines/binary lines to scan when extracting a DOI
# from a PDF (matches the limit used for ``pdf_to_doi``).
_DOI_SCAN_MAXLINES = 200


class IEEEImporter(Importer):
    """Importer from IEEE Xplore URLs or identifiers.

    Unlike the simple ``ArxivImporter`` wrapper, this importer adds extra
    fallback logic in :meth:`fetch_data`. IEEE Xplore's metadata API is
    gated behind an anti-bot challenge that blocks direct requests, so
    BibTeX fetches often return empty. When that happens, the importer
    fetches the article PDF *privately* (without populating
    :attr:`ctx.files`), parses the DOI from it, and queries Crossref for
    the metadata. The actual PDF download for the user's collection is
    left to :meth:`fetch_files`, which runs only when ``--download`` is
    passed, mirroring the clean importer/downloader separation in
    ``ArxivImporter``.
    """

    def __init__(self, uri: str) -> None:
        from papis.downloaders.ieee import IEEEDownloader

        super().__init__(name="ieee", uri=uri)
        self._downloader = IEEEDownloader(uri)

    @classmethod
    def match(cls, uri: str) -> IEEEImporter | None:
        from papis.downloaders.ieee import IEEEDownloader

        down = IEEEDownloader.match(uri)
        if down is not None:
            return IEEEImporter(down.uri)

        return None

    def fetch_data(self) -> None:
        self._downloader.fetch_data()
        self.ctx.data = self._downloader.ctx.data.copy()

        if self.ctx.data:
            return

        self.logger.info(
            "IEEE BibTeX fetch returned no data; "
            "trying DOI-from-PDF fallback via Crossref.")

        doi = self._extract_doi_from_pdf()
        if not doi:
            self.logger.warning(
                "Could not retrieve the PDF or a DOI for IEEE document '%s'. "
                "IEEE Xplore restricts PDF access to networks with an "
                "institutional subscription (e.g. a university VPN or "
                "campus network): this command only works from such a "
                "network. As a workaround, find the article's DOI and run "
                "'papis add --from doi <DOI>' instead.",
                self.uri)
            return

        self.logger.info("Parsed DOI '%s' from the IEEE PDF.", doi)
        data = self._crossref_data(doi)
        if data:
            self.ctx.data = data
            return

        self.logger.warning(
            "Could not retrieve Crossref metadata for DOI '%s' "
            "(IEEE document '%s'). Try 'papis add --from doi %s'.",
            doi, self.uri, doi)

    def fetch_files(self) -> None:
        self._downloader.fetch_files()
        self.ctx.files = self._downloader.ctx.files.copy()

    def _extract_doi_from_pdf(self) -> str | None:
        """Fetch the PDF bytes privately (without touching ``ctx.files``) and
        try to parse a DOI out of them.

        Returns ``None`` if the PDF could not be downloaded or no DOI was
        found. No temporary files are left behind on success.
        """
        from papis.downloaders.ieee import IEEEDownloader

        assert isinstance(self._downloader, IEEEDownloader)

        data = self._downloader.get_document_data()
        if not data:
            return None

        # Paywall / challenge pages are HTML; refuse to DOI-scan them.
        if not self._downloader.check_document_format():
            return None

        # Write to a throw-away temp file so the byte/line-based DOI
        # extractors can be reused, then unlink it immediately.
        fd, path = tempfile.mkstemp(suffix=".pdf")
        try:
            with os.fdopen(fd, "wb") as f:
                f.write(data)
            return self._doi_from_pdf(path)
        finally:
            try:
                os.remove(path)
            except OSError:
                pass

    @staticmethod
    def _doi_from_pdf(path: str) -> str | None:
        if not os.path.isfile(path):
            return None

        from doi import pdf_to_doi

        doi = pdf_to_doi(path, maxlines=_DOI_SCAN_MAXLINES)
        if doi:
            return doi

        # Fallback: scan the raw bytes for a bare DOI pattern. IEEE PDFs
        # embed the DOI in their metadata (e.g. inside /Subject) without a
        # "doi:" prefix, which ``pdf_to_doi`` does not match (it requires
        # surrounding context). Bounded to the same number of lines as the
        # primary scan above.
        import re

        doi_re = re.compile(rb"10\.\d{4,9}/[-._;/:A-Za-z0-9]+")
        with open(path, "rb") as fd:
            for j, line in enumerate(fd):
                m = doi_re.search(line)
                if m:
                    return m.group(0).decode("ascii", errors="ignore").rstrip(".;,")
                if j >= _DOI_SCAN_MAXLINES:
                    break

        return None

    @staticmethod
    def _crossref_data(doi: str) -> dict[str, Any] | None:
        from papis.crossref import get_data

        results = get_data(dois=[doi])
        return results[0] if results else None
