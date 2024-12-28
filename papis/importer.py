from typing import Optional, List, Dict, Any, Callable, Type, TypeVar, TYPE_CHECKING

import papis
import papis.plugin
import papis.logging

if TYPE_CHECKING:
    import stevedore.extension

IMPORTER_EXTENSION_NAME = "papis.importer"

#: Invariant :class:`TypeVar` bound to the :class:`Importer` class.
ImporterT = TypeVar("ImporterT", bound="Importer")


def cache(meth: Callable[[ImporterT], None]) -> Callable[[ImporterT], None]:
    """Decorator used to cache :class:`Importer` methods.

    The data is cached in the :attr:`Importer.ctx` of each importer instance.
    The method *meth* is only called if the context is empty.

    :param meth: a method of an :class:`Importer`.
    """
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
        self.data: Dict[str, Any] = {}
        self.files: List[str] = []

    def __bool__(self) -> bool:
        return bool(self.files) or bool(self.data)


class Importer:
    """
    .. attribute:: name

        A name given to the importer (that is not necessarily unique).

    .. attribute:: uri

        The URI (Uniform Resource Identifier) that the importer is to extract
        data from. This can be an URL, a local or remote file name, an object
        identifier (e.g. DOI), etc.

    .. attribute:: ctx

        A :class:`~papis.importer.Context` that stores the data retrieved by
        the importer.
    """

    def __init__(self,
                 uri: str = "",
                 name: str = "",
                 ctx: Optional[Context] = None) -> None:
        """
        :param uri: uri
        :param name: Name of the importer
        """
        if ctx is None:
            ctx = Context()

        if not name:
            name = type(self).__module__.split(".")[-1]

        self.ctx: Context = ctx
        self.uri: str = uri
        self.name: str = name
        self.logger = papis.logging.get_logger(f"papis.importer.{self.name}")

    @classmethod
    def match(cls, uri: str) -> Optional["Importer"]:
        """Check if the importer can process the given URI.

        For example, an importer that supports links from the arXiv can check
        that the given URI matches using:

        .. code:: python

            re.match(r".*arxiv.org.*", uri)

        This can then be used to instantiate and return a corresponding
        :class:`~papis.importer.Importer` object.

        :param uri: An URI where the document information should be retrieved from.
        :return: An importer instance if the match to the URI is successful or
            *None* otherwise.
        """

        raise NotImplementedError(
            f"Matching URI is not implemented for '{cls.__module__}.{cls.__name__}'"
            )

    @classmethod
    def match_data(cls, data: Dict[str, Any]) -> Optional["Importer"]:
        """Check if the importer can process the given metadata.

        This method can be used to search for valid URIs inside the *data* that
        can then be processed by the importer. For example, if the metadata contains
        a DOI field, this can be used to import additional information.

        :param data: An :class:`dict` with metadata to inspect and match against.
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


def get_import_mgr() -> "stevedore.extension.ExtensionManager":
    """Retrieve the :class:`stevedore.extension.ExtensionManager` for
    importer plugins.
    """
    return papis.plugin.get_extension_manager(IMPORTER_EXTENSION_NAME)


def available_importers() -> List[str]:
    """Get a list of available importer names."""
    return papis.plugin.get_available_entrypoints(IMPORTER_EXTENSION_NAME)


def get_importers() -> List[Type[Importer]]:
    """Get a list of available importer classes."""
    return [e.plugin for e in get_import_mgr()]


def get_importer_by_name(name: str) -> Type[Importer]:
    """Get an importer class by *name*."""
    imp: Type[Importer] = get_import_mgr()[name].plugin
    return imp
