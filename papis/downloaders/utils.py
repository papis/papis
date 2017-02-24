import logging

import papis.downloaders.aps

logger = logging.getLogger("downloader")

DOWNLOADERS = [
        papis.downloaders.aps.Aps
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
