import re
from typing import Any, ClassVar, Dict, Optional

import papis.downloaders.base


class Downloader(papis.downloaders.Downloader):
    DOCUMENT_URL = (
        "https://iopscience.iop.org/article/{doi}/pdf"
        )   # type: ClassVar[str]

    BIBTEX_URL = (
        "https://iopscience.iop.org/export?aid={aid}"
        "&exportFormat=iopexport_bib&exportType=abs"
        "&navsubmit=Export%2Babstract"
        )   # type: ClassVar[str]

    def __init__(self, url: str) -> None:
        super().__init__(
            url, name="iopscience",
            expected_document_extension="pdf",
            priority=10,
            )

    @classmethod
    def match(cls, url: str) -> Optional[papis.downloaders.Downloader]:
        url = re.sub(r"/pdf", "", url)
        if re.match(r".*iopscience\.iop\.org.*", url):
            return Downloader(url)
        else:
            return None

    def get_document_url(self) -> Optional[str]:
        url = self.ctx.data.get("pdf_url")
        if url is not None:
            return str(url)

        doi = self.ctx.data.get("doi")
        if doi is None:
            return None

        url = self.DOCUMENT_URL.format(doi=doi)
        self.logger.debug("Using document URL: '%s'.", url)

        return url

    def _get_article_id(self) -> Optional[str]:
        """
        :returns: aricle ID for IOP.
        """
        doi = self.ctx.data.get("doi")
        if doi is None:
            return None

        return str(doi).replace("10.1088/", "")

    def get_bibtex_url(self) -> Optional[str]:
        aid = self._get_article_id()
        if aid is None:
            return None

        url = self.BIBTEX_URL.format(aid=aid)
        self.logger.debug("Using BibTeX URL: '%s'.", url)
        return url

    def get_data(self) -> Dict[str, Any]:
        soup = self._get_soup()
        data = papis.downloaders.base.parse_meta_headers(soup)

        abstract_nodes = soup.find_all("div", attrs={"class": "wd-jnl-art-abstract"})
        if abstract_nodes:
            data["abstract"] = " ".join(a.text for a in abstract_nodes)

        date = data.get("date")
        if date is not None:
            data["year"] = date.split("-")[0]

        return data
