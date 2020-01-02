from stevedore import extension
import logging
import re

import papis.bibtex
import papis.config
import papis.importer
import papis.plugin

from typing import List

logger = logging.getLogger("downloader")


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
        on_load_failure_callback=papis.plugin.stevedore_error_handler
    )


def get_available_downloaders() -> List[str]:
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


def get_downloaders():
    global downloader_mgr
    _create_downloader_mgr()
    return [e.plugin for e in downloader_mgr.extensions]


def get_info_from_url(url, expected_doc_format=None):
    """Get information directly from url

    :param url: Url of the resource
    :type  url: str
    :param expected_doc_format: override the doc format of the document
    :type  expected_doc_format: str
    :returns: Context object
    :rtype:  papis.importer.Context or None
    """

    downloaders = get_matching_downloaders(url)
    if not downloaders:
        logger.warning(
            "No matching downloader found for (%s)" % url
        )
        return None
    else:
        logger.debug('Found {0} matching downloaders'.format(len(downloaders)))
        downloader = downloaders[0]

    logger.info("Using downloader '%s'" % downloader)
    if downloader.expected_document_extension is None and \
            expected_doc_format is not None:
        downloader.expected_document_extension = expected_doc_format
    downloader.fetch()
    return downloader.ctx


class Importer(papis.importer.Importer):

    """Importer that tries to get data and files from implemented downloaders
    """

    def __init__(self, **kwargs):
        papis.importer.Importer.__init__(self, name='url', **kwargs)

    @classmethod
    def match(cls, uri):
        return (
            Importer(uri=uri)
            if re.match(' *http(s)?.*', uri) is not None
            else None
        )

    def fetch(self):
        self.logger.info("attempting to import from url {0}".format(self.uri))
        self.ctx = get_info_from_url(self.uri)
