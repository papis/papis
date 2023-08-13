import re
from typing import Optional

import papis.downloaders.base


class Downloader(papis.downloaders.Downloader):

    def __init__(self, url: str) -> None:
        super().__init__(url, name="get", priority=0)

    @classmethod
    def match(cls, url: str) -> Optional[papis.downloaders.Downloader]:
        """
        >>> Downloader.match('https://wha2341!@#!@$%!@#file.pdf') is None
        False
        >>> Downloader.match('https://whateverpt?is?therefile.epub') is None
        False
        >>> Downloader.match('https://whatever?path?is?therefile') is None
        True
        """
        endings = "pdf|djvu|epub|mobi|jpg|png|md"
        m = re.match(r"^http.*\.(%s)$" % endings, url, re.IGNORECASE)
        if m:
            d = Downloader(url)

            extension = m.group(1)
            d.expected_document_extensions = (extension,)
            d.logger.info("Expecting a document of type '%s'.", extension)

            return d
        else:
            return None

    def get_document_url(self) -> Optional[str]:
        return self.uri
