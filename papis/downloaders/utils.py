import logging

import papis.downloaders.aps
import papis.downloaders.arxiv

logger = logging.getLogger("downloader")

DOWNLOADERS = [
        papis.downloaders.aps.Aps,
        papis.downloaders.arxiv.Arxiv,
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
