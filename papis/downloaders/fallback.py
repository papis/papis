from typing import Dict, Any, Optional, List, Union

import papis.downloaders.base


class Downloader(papis.downloaders.Downloader):

    def __init__(self, uri: str, name: str = "fallback",
                 expected_document_extension: Optional[Union[str, List[str]]] = None,
                 priority: int = -1,
                 ) -> None:
        super().__init__(
            uri, name,
            expected_document_extension=expected_document_extension,
            priority=priority,
            )

    @classmethod
    def match(cls, url: str) -> Optional[papis.downloaders.Downloader]:
        return Downloader(url)

    def get_data(self) -> Dict[str, Any]:
        soup = self._get_soup()
        data = papis.downloaders.base.parse_meta_headers(soup)

        if "url" not in data:
            data["url"] = self.uri

        return data

    def get_doi(self) -> Optional[str]:
        if self.ctx.data:
            doi = self.ctx.data.get("doi")
            if doi:
                return str(doi)

        from doi import find_doi_in_text
        soup = self._get_soup()
        return find_doi_in_text(str(soup))

    def get_document_url(self) -> Optional[str]:
        url = self.ctx.data.get("pdf_url")
        if url is not None:
            self.logger.debug("Using document URL: '%s'.", url)

        return str(url)
