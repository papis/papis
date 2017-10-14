import logging

import tempfile
import papis.bibtex
import papis.config

logger = logging.getLogger("downloader")


def getAvailableDownloaders():
    import papis.downloaders.aps
    import papis.downloaders.acs
    import papis.downloaders.arxiv
    import papis.downloaders.scitationaip
    import papis.downloaders.annualreviews
    import papis.downloaders.iopscience
    import papis.downloaders.libgen
    import papis.downloaders.get
    return [
        papis.downloaders.aps.Downloader,
        papis.downloaders.acs.Downloader,
        papis.downloaders.arxiv.Downloader,
        papis.downloaders.scitationaip.Downloader,
        papis.downloaders.annualreviews.Downloader,
        papis.downloaders.iopscience.Downloader,
        papis.downloaders.libgen.Downloader,
        papis.downloaders.get.Downloader,
    ]


def get_downloader(url, downloader=False):
    """Get downloader object. If only a url is given, the url is matched
    against the match method of the downloaders.

    :param url: Url of the document
    :type  url: str
    :param downloader: Name of the downloader, if any.
    :type  downloader: str

    """
    if not downloader:
        for downloader in getAvailableDownloaders():
            result = downloader.match(url)
            if result:
                return result
    else:
        try:
            mod = __import__(
                'papis.downloaders.%s' % downloader,
                fromlist=['Downloader']
            )
            return getattr(mod, 'Downloader')(url)
        except ImportError:
            logger.error("No downloader named %s" % downloader)
    return False


def download_document_from_doi(doi):
    """Download a document knowing the doi number

    :param doi: Doi number
    :type  doi: string
    :returns: Path to downloaded local document

    """
    tempf = tempfile.mktemp()
    external_downloader = papis.config.get(
        "doc-doi-downloader"
    )



def get(url, data_format="bibtex", expected_doc_format=None):
    logger.debug("Attempting to retrieve from url")
    result = {
        "data": dict(),
        "doi": None,
        "documents_paths": []
    }
    downloader = get_downloader(url)
    if not downloader:
        logger.warning(
            "No matching Downloader for the url %s found" % url
        )
        return result
    logger.debug("Using downloader %s" % downloader)
    if downloader.expected_document_format is None and \
            expected_doc_format is not None:
        downloader.expected_document_format = expected_doc_format
    try:
        doi = downloader.get_doi()
    except:
        logger.debug("Doi not found from url...")
    if data_format == "bibtex":
        try:
            bibtex_data = downloader.get_bibtex_data()
            if bibtex_data:
                result["data"] = papis.bibtex.bibtex_to_dict(
                    bibtex_data
                )
                result["data"] = result["data"][0] \
                    if len(result["data"]) > 0 else dict()
        except NotImplementedError:
            pass
    try:
        doc_data = downloader.get_document_data()
    except NotImplementedError:
        doc_data = False
    if doc_data:
        if downloader.check_document_format():
            result["documents_paths"].append(tempfile.mktemp())
            logger.debug(
                "Saving downloaded data in %s" % result["documents_paths"][-1]
            )
            with open(result["documents_paths"][-1], "wb+") as fd:
                fd.write(doc_data)
    return result
