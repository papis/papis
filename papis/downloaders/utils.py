import logging

import papis.downloaders.aps
import papis.downloaders.arxiv
import papis.downloaders.scitationaip
import papis.downloaders.libgen
import papis.downloaders.get

logger = logging.getLogger("downloader")

DOWNLOADERS = [
        papis.downloaders.aps.Aps,
        papis.downloaders.arxiv.Arxiv,
        papis.downloaders.scitationaip.Downloader,
        papis.downloaders.libgen.Downloader,
        papis.downloaders.get.Get,
        ]


def getDownloader(url):
    """TODO: Docstring for getDownloader.

    :url: TODO
    :returns: TODO

    """
    global DOWNLOADERS
    for downloader in DOWNLOADERS:
        result = downloader.match(url)
        if result:
            return result
    return False
