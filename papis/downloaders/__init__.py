from stevedore import extension
import papis.config
import logging
import tempfile
import papis.bibtex
import papis.config

logger = logging.getLogger("downloader")


def stevedore_error_handler(manager, entrypoint, exception):
    logger = logging.getLogger('cmds:stevedore')
    logger.error("Error while loading entrypoint [%s]" % entrypoint)
    logger.error(exception)


downloader_mgr = None


def _create_downloader_mgr():
    global downloader_mgr

    if downloader_mgr is not None:
        return

    downloader_mgr = extension.ExtensionManager(
        namespace='papis.downloader',
        invoke_on_load=False,
        verify_requirements=True,
        propagate_map_exceptions=True,
        on_load_failure_callback=stevedore_error_handler
    )


def get_available_downloaders():
    global downloader_mgr
    _create_downloader_mgr()
    return [e.plugin for e in downloader_mgr.extensions]


def get_downloader(url, downloader=''):
    """Get downloader object. If only a url is given, the url is matched
    against the match method of the downloaders.

    :param url: Url of the document
    :type  url: str
    :param downloader: Name of a downloader
    :type  downloader: str
    :returns: A Downloader if found or none
    :rtype:  papis.downloader.base.Downloader
    :raises KeyError: If no downloader is found

    """
    global downloader_mgr
    _create_downloader_mgr()
    assert(isinstance(downloader, str))
    if downloader:
        return get_downloader_by_name(downloader)(url)
    else:
        return get_matching_downloaders(url)[0]


def get_matching_downloaders(url):
    """Get matching downloaders sorted by their priorities.
    The first elements have the higher priority

    :param url: Url to be matched against
    :type  url: str
    :returns: A list of sorted downloaders
    :rtype: list
    """
    global downloader_mgr
    _create_downloader_mgr()
    return sorted(
        filter(
            lambda d: d,
            [d.match(url) for d in get_available_downloaders()]
        ),
        key=lambda k: k.priority,
        reverse=True
    )


def get_downloader_by_name(name):
    """Get a downloader by its name

    :param name: Name of the downloader
    :type  name: str
    :returns: A downloader class
    :rtype:  papis.base.Downloader
    """
    global downloader_mgr
    _create_downloader_mgr()
    return downloader_mgr[name].plugin


def get_info_from_url(url, data_format="bibtex", expected_doc_format=None):

    result = {
        "data": dict(),
        "doi": None,
        "documents_paths": []
    }

    downloaders = get_matching_downloaders(url)
    if not downloaders:
        logger.warning(
            "No matching downloader found (%s)" % url
        )
        return result
    else:
        logger.debug('Found {0} matching downloaders'.format(len(downloaders)))
        downloader = downloaders[0]

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
                "Saving downloaded file in %s" % result["documents_paths"][-1]
            )
            with open(result["documents_paths"][-1], "wb+") as fd:
                fd.write(doc_data)

    return result
