from stevedore import extension
import logging
import re

import papis.bibtex
import papis.config
import papis.importer
import papis.plugin

from typing import List, Optional, Any, Sequence

logger = logging.getLogger("downloader")


def _extension_name() -> str:
    return "papis.downloader"


def get_available_downloaders() -> List[papis.importer.Importer]:
    return papis.plugin.get_available_plugins(_extension_name())


def get_matching_downloaders(url: str) -> Sequence[papis.importer.Importer]:
    """Get matching downloaders sorted by their priorities.
    The first elements have the higher priority

    :param url: Url to be matched against
    :type  url: str
    :returns: A list of sorted downloaders
    :rtype: list
    """
    matches = list(filter(lambda d: d is not None,
        [d.match(url) for d in get_available_downloaders()]
    ))  # type: List[papis.importer.Importer]
    return sorted(
        matches,
        key=lambda k: k.priority,
        reverse=True)


def get_downloader_by_name(name: str) -> papis.importer.Importer:
    """Get a downloader by its name

    :param name: Name of the downloader
    :type  name: str
    :returns: A downloader class
    :rtype:  papis.base.Downloader
    """
    downloader_mgr = papis.plugin.get_extension_manager(_extension_name())
    return downloader_mgr[name].plugin


def get_info_from_url(
        url: str,
        expected_doc_format: Optional[str] = None
        ) -> papis.importer.Context:
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
        return papis.importer.Context()
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

    def __init__(self, **kwargs: Any):
        papis.importer.Importer.__init__(self, name='url', **kwargs)

    @classmethod
    def match(cls, uri: str) -> Optional[papis.importer.Importer]:
        return (
            Importer(uri=uri)
            if re.match(' *http(s)?.*', uri) is not None
            else None
        )

    def fetch(self) -> None:
        self.logger.info("attempting to import from url {0}".format(self.uri))
        self.ctx = get_info_from_url(self.uri) or papis.importer.Context()
