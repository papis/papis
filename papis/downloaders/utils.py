import logging

import papis.downloaders.aps

logger = logging.getLogger("downloader")

def getDownloader(url):
    """TODO: Docstring for getDownloader.

    :url: TODO
    :returns: TODO

    """
    if re.match(r".*aps.org.*", url):
        logger.info("Downloading from aps.org...")
        return aps.Aps(url)
