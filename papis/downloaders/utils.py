import logging

import tempfile
import papis.bibtex
import papis.config

logger = logging.getLogger("downloader")


def get_available_downloaders():
    names = [
        "aps", "acs", "arxiv", "ieee", "scitationaip", "annualreviews",
        "iopscience", "libgen", "get", "thesesfr", "hal", "frontiersin",
        "worldscientific",
    ]
    downloaders = []
    for name in names:
        mod = __import__(
            'papis.downloaders.' + name,
            fromlist=['Downloader']
        )
        downloaders.append(getattr(mod, 'Downloader'))
    return downloaders


def get_downloader(url, downloader=False):
    """Get downloader object. If only a url is given, the url is matched
    against the match method of the downloaders.

    :param url: Url of the document
    :type  url: str
    :param downloader: Name of a downloader
    :type  downloader: str
    :returns: A Downloader if found or none
    :rtype:  papis.downloader.base.Downloader

    """
    if not downloader:
        for downloader in get_available_downloaders():
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


def get(url, data_format="bibtex", expected_doc_format=None):

    result = {
        "data": dict(),
        "doi": None,
        "documents_paths": []
    }

    downloader = get_downloader(url)
    if not downloader:
        logger.warning(
            "No matching downloader found (%s)" % url
        )
        return result

    logger.info("Using downloader '%s'" % downloader)
    if downloader.expected_document_extension is None and \
            expected_doc_format is not None:
        downloader.expected_document_extension = expected_doc_format

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
        doc_data = None

    try:
        result['doi'] = downloader.get_doi()
    except NotImplementedError:
        pass

    if doc_data is not None:
        if downloader.check_document_format():
            result["documents_paths"].append(tempfile.mktemp())
            logger.info(
                "Saving downloaded data in %s" % result["documents_paths"][-1]
            )
            with open(result["documents_paths"][-1], "wb+") as fd:
                fd.write(doc_data)

    return result
