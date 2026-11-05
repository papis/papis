from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeVar

import papis.logging

if TYPE_CHECKING:
    from collections.abc import Callable

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
    def match(cls, uri: str) -> Importer | None:
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
    def match_data(cls, data: dict[str, Any]) -> Importer | None:
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

        This method calls :meth:`~papis.importer.Importer.fetch_data` and
        :meth:`~papis.importer.Importer.fetch_files` to get all the information
        available for the document. It is recommended to implement the two
        methods separately, if possible, for maximum flexibility.

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
