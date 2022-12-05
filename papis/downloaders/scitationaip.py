import re
from typing import Optional

import papis.downloaders.base


class Downloader(papis.downloaders.Downloader):

    def __init__(self, url: str) -> None:
        super().__init__(
            url, name="scitationaip",
            expected_document_extension="pdf",
            )

    @classmethod
    def match(cls, url: str) -> Optional[papis.downloaders.Downloader]:
        # http://aip.scitation.org/doi/10.1063/1.4873138
        if re.match(r".*(aip|aapt)\.scitation\.org.*", url):
            return Downloader(url)
        else:
            return None

    def get_doi(self) -> Optional[str]:
        mdoi = re.match(r".*/doi/(.*/[^?&%^$]*).*", self.uri)
        if mdoi:
            doi = mdoi.group(1).replace("abs/", "").replace("full/", "")
            return doi
        else:
            return None

    def get_document_url(self) -> Optional[str]:
        # http://aip.scitation.org/doi/pdf/10.1063/1.4873138
        durl = ("http://aip.scitation.org/doi/pdf/{doi}"
                .format(doi=self.get_doi()))
        self.logger.debug("doc url = '%s'", durl)
        return durl

    def get_bibtex_url(self) -> Optional[str]:
        url = ("http://aip.scitation.org/action/downloadCitation"
               "?format=bibtex&cookieSet=1&doi={doi}"
               .format(doi=self.get_doi()))
        self.logger.debug("bibtex url = '%s'", url)
        return url
