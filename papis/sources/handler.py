"""Source-handler basics: data types, base class, and registry."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, ClassVar, Literal, get_args

import papis.logging

if TYPE_CHECKING:
    from collections.abc import Iterator

    from papis.document import DocumentLike

logger = papis.logging.get_logger(__name__)

#: Name of the entry-point namespace for :class:`SourceHandler` plugins.
SOURCE_NAMESPACE_NAME = "papis.source"

#: What the item of a lookup refers to
LookupItemKind = Literal["file", "webpage"]


@dataclass
class LookupInput:
    """Evidence for the lookup flow.

    :param input: the user input string.
    :param kind: what :attr:`input` refers to. ``None`` when it is just text.
    :param content: text read from the item.
    :param fields: extracted metadata (e.g. identifiers) as text.
    """

    input: str = ""
    kind: LookupItemKind | None = None
    content: str | None = None
    fields: dict[str, str] = field(default_factory=dict)


@dataclass
class SearchInput:
    """The constraints for the search flow.

    :param input: the free-text query string.
    :param filters: constraints on document fields.
    """

    input: str = ""
    filters: dict[str, list[str]] = field(default_factory=dict)


@dataclass
class ParseInput:
    """The content to parse into documents.

    :param content: the text to parse.
    """

    content: str = ""


@dataclass
class FileReference:
    """A reference to a file associated with a document.

    :param url: a remote file to download.
    :param path: a local file (used by the legacy adapter).
    :param filename: a suggested name for the file.
    :param extension: the expected extension of the remote file (or any if ``None``).
    """

    url: str | None = None
    path: str | None = None
    filename: str | None = None
    extension: str | None = None


@dataclass
class Followup:
    """A request for further evidence emitted by a source handler.

    Source handlers may ask for the download of further metadata. They do not download
    themselves since they might run into bot blocks.

    :param url: the URL to download.
    :param format: name of format handler that should parse the downloaded content.
    :param priority: priority for the parsed result.
    """

    url: str
    format: str
    priority: int


#: Handler capabilities (``lookup`` is required of every handler).
Capability = Literal["lookup", "search", "parse"]


@dataclass
class LookupOutput:
    """A handler's answer to a lookup.

    A handler may answer with only :attr:`files` and no :attr:`document` when the
    metadata needs to be downloaded in a :attr:`followup`.

    :param document: the retrieved document.
    :param files: references to files to attach to the document.
    :param followup: a request for further evidence.
    :param message: the handler's message, if any.
    """

    document: DocumentLike | None = None
    files: list[FileReference] = field(default_factory=list)
    followup: Followup | None = None
    message: str | None = None


@dataclass
class SearchOutput:
    """A handler's answer to a search.

    :param documents: the found documents.
    :param message: the handler's message, if any.
    """

    documents: list[DocumentLike] = field(default_factory=list)
    message: str | None = None


@dataclass
class ParseOutput:
    """A handler's answer to a parse.

    :param documents: the parsed documents.
    :param message: the handler's message, if any.
    """

    documents: list[DocumentLike] = field(default_factory=list)
    message: str | None = None


class SourceHandler(ABC):
    """Base class for source-handler plugins.

    Subclasses must, at a minimum, set :attr:`name` and implement
    :meth:`match_for_lookup` and :meth:`lookup`.
    """

    #: Name of the handler.
    name: ClassVar[str]
    #: Priority of the handler's results (higher wins when merging).
    priority: ClassVar[int] = 5
    #: Handler capabilities (derived automatically).
    capabilities: ClassVar[frozenset[Capability]] = frozenset()
    #: Fields this handler uses when searching. Empty if free-text only.
    search_fields: ClassVar[tuple[str, ...]] = ()

    # NOTE: runs on every subclass definition to derive 'capabilities' from the methods
    # the subclass overrides.
    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        cls.capabilities = frozenset(
            name
            for name in get_args(Capability)
            if any(
                name in base.__dict__
                for base in cls.__mro__
                if base is not SourceHandler
            )
        )

    def __init__(self) -> None:
        self.logger = papis.logging.get_logger(f"papis.source.{self.name}")

    @classmethod
    @abstractmethod
    def match_for_lookup(cls, evidence: LookupInput) -> SourceHandler | None:
        """Return a handler instance if it can use *evidence* for :meth:`lookup`.

        If possible, matching has no IO (especially network requests) because these may
        be blocked and slow down Papis when many source handlers may be tried.
        """

    @abstractmethod
    def lookup(self, evidence: LookupInput) -> LookupOutput:
        """Fetch and return data for a single document."""

    @classmethod
    def search(cls, query: SearchInput, *, max_results: int) -> SearchOutput:
        """Search the source for documents matching *query*."""
        raise NotImplementedError(f"handler '{cls.name}' does not implement search")

    @classmethod
    def parse(cls, content: str) -> ParseOutput | None:
        """Parse *content* into Papis documents."""
        raise NotImplementedError(f"handler '{cls.name}' does not parse content")


def discover_handlers() -> dict[str, type[SourceHandler]]:
    """Discover all handlers

    :returns: discovered handler classes keyed by :attr:`SourceHandler.name`.
    """
    from papis.plugin import get_plugins
    from papis.sources.legacy import wrap_legacy_plugins

    claimed_names: set[str] = set()
    handlers: dict[str, type[SourceHandler]] = {}
    for name, cls in get_plugins(SOURCE_NAMESPACE_NAME).items():
        if not (isinstance(cls, type) and issubclass(cls, SourceHandler)):
            logger.warning(
                "Ignoring source handler '%s': not a SourceHandler subclass.", name
            )
            continue

        if cls.name in claimed_names:
            logger.warning(
                "Ignoring source handler '%s': name is already claimed.",
                cls.name,
            )
            continue

        claimed_names.add(cls.name)
        handlers[cls.name] = cls

    legacy_names: list[str] = []
    for name, cls in wrap_legacy_plugins().items():
        if name not in claimed_names:
            claimed_names.add(name)
            handlers[name] = cls
            legacy_names.append(name)

    if legacy_names:
        logger.warning(
            "Legacy importer/downloader plugins are deprecated and will be "
            "removed in Papis 0.18: '%s'. Migrate them to the source-handler API.",
            "', '".join(sorted(legacy_names)),
        )

    return handlers


class HandlerRegistry:
    """Source handler registry."""

    def __init__(self) -> None:
        self._handlers: dict[str, type[SourceHandler]] = {}
        self._loaded = False

    def load(self) -> None:
        """Discover and register all handlers."""
        if self._loaded:
            return

        self._loaded = True
        self._handlers = discover_handlers()

    def get(self, name: str) -> type[SourceHandler] | None:
        """Get the handler registered under *name*."""
        self.load()
        return self._handlers.get(name)

    def __iter__(self) -> Iterator[type[SourceHandler]]:
        """Iterate over all registered handler classes, in registration order."""
        self.load()
        return iter(list(self._handlers.values()))


registry = HandlerRegistry()
