from __future__ import annotations

from typing import Any

from papis.downloaders import Downloader


class FallbackDownloader(Downloader):
    """Retrieve documents from websites using Dublin Core or Google Scholar metadata"""

    def __init__(self, uri: str, name: str = "fallback",
                 expected_document_extension: str | list[str] | None = None,
                 priority: int = -1,
                 ) -> None:
        super().__init__(
            uri, name,
            expected_document_extension=expected_document_extension,
            priority=priority,
            )

    @classmethod
    def match(cls, url: str) -> Downloader | None:
        return FallbackDownloader(url)

    def get_data(self) -> dict[str, Any]:
        from papis.downloaders.base import parse_meta_headers

        soup = self._get_soup()
        data = parse_meta_headers(soup)

        if "url" not in data:
            data["url"] = self.uri

        return data

    def get_doi(self) -> str | None:
        if self.ctx.data:
            doi = self.ctx.data.get("doi")
            if doi:
                return str(doi)

        from doi import find_doi_in_text
        soup = self._get_soup()
        return find_doi_in_text(str(soup))

    def get_document_url(self) -> str | None:
        url = self.ctx.data.get("pdf_url")
        if url is not None:
            self.logger.debug("Using document URL: '%s'.", url)

        return str(url)
