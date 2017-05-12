import logging

import papis.downloaders.aps
import papis.downloaders.arxiv
import papis.downloaders.scitationaip
import papis.downloaders.libgen
import papis.downloaders.get

logger = logging.getLogger("downloader")

def getAvailableDownloaders():
    return [
        papis.downloaders.aps.Downloader,
        papis.downloaders.arxiv.Downloader,
        papis.downloaders.scitationaip.Downloader,
        papis.downloaders.libgen.Downloader,
        papis.downloaders.get.Downloader,
    ]



def getDownloader(url):
    for downloader in getAvailableDownloaders():
        result = downloader.match(url)
        if result:
            return result
    return False
