from collections.abc import Callable, Iterable
from typing import Any, TypeVar

import papis.logging

logger = papis.logging.get_logger(__name__)

ImporterT = TypeVar("ImporterT", bound="Importer")

#: Name of the entry point namespace for :class:`Importer` plugins.
IMPORTER_NAMESPACE_NAME = "papis.importer"


def cache(meth: Callable[[ImporterT], None]) -> Callable[[ImporterT], None]:
    from functools import wraps

    @wraps(meth)
    def wrapper(self: ImporterT) -> None:
        if not self.ctx:
            meth(self)

    return wrapper


class Context:
    """
    .. attribute:: data

        A :class:`dict` of fields retrieved by the :class:`Importer`. These are
        generally not processed.

    .. attribute:: files

        A :class:`list` of files retrieved by the :class:`Importer`.
    """

    def __init__(self) -> None:
        self.data: dict[str, Any] = {}
        self.files: list[str] = []

    def __bool__(self) -> bool:
        return bool(self.files) or bool(self.data)


class Importer:
    """A base class for Papis importer plugins."""

    #: A name given to the importer (that is not necessarily unique).
    name: str
    #: The URI (Uniform Resource Identifier) that the importer is to extract
    #: data from. This can be an URL, a local or remote file name, an object
    #: identifier (e.g. DOI), etc.
    uri: str
    #: A :class:`~papis.importer.Context` that stores the data retrieved by
    #: the importer.
    ctx: Context

    def __init__(self,
                 uri: str = "",
                 name: str = "",
                 ctx: Context | None = None) -> None:
        if ctx is None:
            ctx = Context()

        if not name:
            name = type(self).__module__.split(".")[-1]

        self.name = name
        self.uri = uri
        self.ctx = ctx
        self.logger = papis.logging.get_logger(f"papis.importer.{self.name}")

    @classmethod
    def match(cls, uri: str) -> "Importer | None":
        """Check if the importer can process the given URI.

        For example, an importer that supports links from arXiv can check that
        the given URI matches using:

        .. code:: python

            re.match(r".*arxiv.org.*", uri)

        This can then be used to instantiate and return a corresponding
        :class:`~papis.importer.Importer` object.

        :param uri: An URI from which the document metadata should be retrieved.
        :return: An importer instance if the match to the URI is successful or
            *None* otherwise.
        """

        raise NotImplementedError(
            f"Matching URIs is not implemented for '{cls.__module__}.{cls.__name__}'"
            )

    @classmethod
    def match_data(cls, data: dict[str, Any]) -> "Importer | None":
        """Check if the importer can process the given metadata.

        This method can be used to search for valid URIs inside the *data* that
        can then be processed by the importer. For example, if the metadata contains
        a DOI field, this can be used to import additional information.

        :param data: A :class:`dict` with metadata to inspect and match against.
        :return: An importer instance if matching metadata is found or
            *None* otherwise.
        """
        raise NotImplementedError(
            "Matching metadata is not implemented for "
            f"'{cls.__module__}.{cls.__name__}'")

    @cache
    def fetch(self) -> None:
        """Fetch metadata and files for the given :attr:`~papis.importer.Importer.uri`.

        This method calls :meth:`Importer.fetch_data` and :meth:`Importer.fetch_files`
        to get all the information available for the document. It is recommended
        to implement the two methods separately, if possible, for maximum
        flexibility.

        The imported data is stored in :attr:`~papis.importer.Importer.ctx` and
        it is not queried again on subsequent calls to this function.
        """
        from contextlib import suppress

        with suppress(NotImplementedError):
            self.fetch_data()

        with suppress(NotImplementedError):
            self.fetch_files()

    def fetch_data(self) -> None:
        """Fetch metadata from the given :attr:`~papis.importer.Importer.uri`.

        The imported metadata is stored in :attr:`~papis.importer.Importer.ctx`.
        """
        raise NotImplementedError(
            "Fetching metadata is not implemented for "
            f"'{type(self).__module__}.{type(self).__name__}'")

    def fetch_files(self) -> None:
        """Fetch files from the given :attr:`~papis.importer.Importer.uri`.

        The imported files are stored in :attr:`~papis.importer.Importer.ctx`.
        """
        raise NotImplementedError(
            "Fetching files is not implemented for "
            f"'{type(self).__module__}.{type(self).__name__}'")

    def __str__(self) -> str:
        return f"{type(self).__name__}({self.name}, uri={self.uri})"


def get_available_importers() -> list[str]:
    """Get a list of available importer names."""
    from papis.plugin import get_plugin_names

    return get_plugin_names(IMPORTER_NAMESPACE_NAME)


def get_importer_by_name(name: str) -> type[Importer]:
    """Get an importer class by *name*."""
    from papis.plugin import InvalidPluginTypeError, get_plugin_by_name

    cls = get_plugin_by_name(IMPORTER_NAMESPACE_NAME, name)
    if not issubclass(cls, Importer):
        raise InvalidPluginTypeError(IMPORTER_NAMESPACE_NAME, name)

    return cls  # type: ignore[no-any-return]


def get_matching_importers_by_name(
        name_and_uris: Iterable[tuple[str, str]], *,
        include_downloaders: bool = False,
    ) -> list[Importer]:
    """Get importers that match the given names.

    This function tries to match the URI using :meth:`~Importer.match` for each
    importer in *name_and_uris*. All matching importers are then returned, but
    no data is fetched (see :func:`fetch_importers`).

    :param name_and_uris: an iterable of ``(name, uri)`` tuples that describe the
        importer names and URIs to match them against.
    :param include_downloaders: if *True*, downloader plugins are also included
        when matching the given names and URIs.
    """
    if not name_and_uris:
        return []

    from papis.plugin import get_plugins

    def match(namespace: str) -> list[Importer]:
        plugins = get_plugins(namespace)

        importers = []
        for name, uri in name_and_uris:
            cls = plugins.get(name)
            if cls is None:
                logger.error("Unknown importer '%s' for URI '%s'.", name, uri)
                continue

            if not issubclass(cls, Importer):
                logger.error(
                    "Plugin '%s' for namespace '%s' does not subclass 'Importer': %s.",
                    name, IMPORTER_NAMESPACE_NAME, cls
                )
                continue

            try:
                importer = cls.match(uri)
            except NotImplementedError:
                logger.error("Importer '%s.%s' does not implement matching.",
                             cls.__module__, cls.__name__)
                continue

            if importer is None:
                logger.warning("Importer '%s.%s' does not match URI: '%s'.",
                               cls.__module__, cls.__name__, uri)
                continue

            logger.debug("Matched importer '%s.%s' for URI '%s'.",
                         cls.__module__, cls.__name__, uri)
            importers.append(importer)

        return importers

    result = match(IMPORTER_NAMESPACE_NAME)
    if include_downloaders:
        from papis.downloaders import DOWNLOADERS_EXTENSION_NAME
        result.extend(match(DOWNLOADERS_EXTENSION_NAME))

    return result


def get_matching_importers_by_uri(
        uri: str, *,
        include_downloaders: bool = False,
    ) -> list[Importer]:
    """Get importers that match the given URI.

    This function tries to match the URI using :meth:`~Importer.match` for all
    known importers. All matching importers are then returned, but no data is
    fetched (see :func:`fetch_importers`).

    :param include_downloaders: if *True*, downloader plugins are also included
        when matching the given URI.
    """
    from papis.plugin import get_plugins

    def match(namespace: str) -> list[Importer]:
        plugins = get_plugins(namespace)

        importers = []
        for name, cls in plugins.items():
            if not issubclass(cls, Importer):
                logger.error(
                    "Plugin '%s' for namespace '%s' does not subclass 'Importer': %s.",
                    name, IMPORTER_NAMESPACE_NAME, cls
                )
                continue

            try:
                importer = cls.match(uri)
            except NotImplementedError:
                logger.debug("Importer '%s.%s' failed to match URI '%s'.",
                             cls.__module__, cls.__name__, uri)
                continue

            if importer is None:
                logger.debug("Importer '%s.%s' failed to match URI '%s'.",
                             cls.__module__, cls.__name__, uri)
                continue

            logger.debug("Matched importer '%s.%s' for URI '%s'.",
                         cls.__module__, cls.__name__, uri)
            importers.append(importer)

        return importers

    result = match(IMPORTER_NAMESPACE_NAME)
    if include_downloaders:
        from papis.downloaders import DOWNLOADERS_EXTENSION_NAME
        result.extend(match(DOWNLOADERS_EXTENSION_NAME))

    return result


def get_matching_importers_by_doc(
        doc: "papis.document.DocumentLike", *,
        include_downloaders: bool = False,
    ) -> list[Importer]:
    """Get importers that match the given document.

    This function tries to match the document using :meth:`~Importer.match_data`.
    All matching importers are then returned, but no data is fetched
    (see :func:`fetch_importers`).

    :param doc: a dictionary containing document metadata.
    :param include_downloaders: if *True*, downloader plugins are also included
        when matching the given URI.
    """
    from papis.document import describe

    descr = describe(doc)

    from papis.plugin import get_plugins

    def match(namespace: str) -> list[Importer]:
        plugins = get_plugins(namespace)

        importers = []
        for name, cls in plugins.items():
            if not issubclass(cls, Importer):
                logger.error(
                    "Plugin '%s' for namespace '%s' does not subclass 'Importer': %s.",
                    name, IMPORTER_NAMESPACE_NAME, cls
                )
                continue

            try:
                importer = cls.match_data(doc)
            except NotImplementedError:
                logger.debug("Importer '%s.%s' failed to match document: '%s'.",
                             cls.__module__, cls.__name__, descr)
                continue

            if importer is None:
                logger.debug("Importer '%s.%s' failed to match document: '%s'.",
                             cls.__module__, cls.__name__, descr)
                continue

            logger.debug("Matched importer '%s.%s' for document: '%s'.",
                         cls.__module__, cls.__name__, descr)
            importers.append(importer)

        return importers

    result = match(IMPORTER_NAMESPACE_NAME)
    if include_downloaders:
        from papis.downloaders import DOWNLOADERS_EXTENSION_NAME
        result.extend(match(DOWNLOADERS_EXTENSION_NAME))

    return result


def fetch_importers(importers: Iterable[Importer], *,
                    download_files: bool = True) -> list[Importer]:
    """Fetch data from the given importers.

    :param download_files: if *True*, importers also try to download files
        (PDFs, etc.) instead of just metadata.
    :returns: a list of importers that have not failed to fetch their metadata.
    """
    if not importers:
        return []

    from requests.exceptions import RequestException

    result = []
    for importer in importers:
        try:
            if download_files:
                importer.fetch()
            else:
                # NOTE: not all importers can (or do) separate the fetching
                # of data and files, so we try both cases for now
                try:
                    importer.fetch_data()
                except NotImplementedError:
                    importer.fetch()
        except RequestException as exc:
            # NOTE: this is probably some HTTP error, so we better let the
            # user know if there's something wrong with their network
            logger.error("Network error! Failed to fetch data from importer "
                         "'%s': '%s'.", importer.name, importer.uri, exc_info=exc)
        except Exception as exc:
            logger.debug("Fetch Error! Failed to fetch data from importer "
                         "'%s': '%s'.", importer.name, importer.uri, exc_info=exc)
        else:
            logger.debug("Fetched data from importer: %s", importer)
            result.append(importer)

    return result


def collect_from_importers(
        importers: Iterable[Importer],
        *,
        batch: bool = True,
        use_files: bool = True,
        ) -> Context:
    """Collect all data from the given *importers*.

    It is assumed that the importers have called the needed ``fetch`` methods,
    so all data has been downloaded and converted (see :func:`fetch_importers`).
    This function is meant to only do the aggregation.

    :param batch: if *True*, overwrite data from previous importers, otherwise
        ask the user to manually merge. Note that files are always kept, even
        if they potentially contain duplicates.
    :param use_files: if *True*, both metadata and files are collected
        from the importers.
    """
    result = Context()
    if not importers:
        return result

    from papis.utils import update_doc_from_data_interactively

    for importer in importers:
        ctx = importer.ctx

        if ctx.data:
            logger.info("Merging data from importer '%s'.", importer.name)
            if batch:
                result.data.update(ctx.data)
            else:
                if result.data:
                    update_doc_from_data_interactively(
                        result.data,
                        ctx.data,
                        str(importer))
                else:
                    # NOTE: first importer does not require interactive use
                    result.data.update(ctx.data)

        if use_files and ctx.files:
            logger.info("Got files from importer '%s':\n\t%s",
                        importer.name,
                        "\n\t".join(ctx.files))

            result.files.extend(ctx.files)

    return result


# DEPRECATED

def available_importers() -> list[str]:
    from warnings import warn

    warn("'papis.importer.available_importers' is deprecated and will be "
         "removed in Papis v0.16. Use 'papis.importer.get_available_importers' "
         "instead.", DeprecationWarning, stacklevel=2)

    return get_available_importers()


def get_importers() -> list[type[Importer]]:
    """Get a list of available importer classes."""
    from papis.plugin import get_plugins

    return list(get_plugins(IMPORTER_NAMESPACE_NAME).values())
