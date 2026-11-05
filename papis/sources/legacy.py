"""Adapter for legacy importers and downloaders."""

from __future__ import annotations

from typing import TYPE_CHECKING

import papis.config
import papis.logging
from papis.sources.handler import (
    FileReference,
    LookupOutput,
    SourceHandler,
)

if TYPE_CHECKING:
    from papis.importer import Importer
    from papis.sources.handler import LookupInput

logger = papis.logging.get_logger(__name__)


def wrap_legacy_plugin(
    plugin_name: str, importer_cls: type[Importer]
) -> type[SourceHandler]:
    """Wrap a legacy importer/downloader in a :class:`SourceHandler`."""

    class LegacySourceHandler(SourceHandler):
        name = plugin_name
        is_legacy = True

        def __init__(self, importer: Importer) -> None:
            super().__init__()
            self.importer = importer

        @classmethod
        def match_for_lookup(cls, evidence: LookupInput) -> LegacySourceHandler | None:
            importer = None
            try:
                importer = importer_cls.match(evidence.input)
            except NotImplementedError:
                pass

            if importer is None:
                try:
                    importer = importer_cls.match_data(dict(evidence.fields))
                except NotImplementedError:
                    pass

            if importer is None:
                return None

            return cls(importer)

        def lookup(self, evidence: LookupInput) -> LookupOutput:
            self.importer.fetch()

            data = dict(self.importer.ctx.data)
            pdf_url = data.pop("pdf_url", None)
            if pdf_url is not None:
                data[papis.config.getstring("doc-url-key-name")] = pdf_url

            document = data if data else None
            files = [FileReference(path=path) for path in self.importer.ctx.files]

            return LookupOutput(
                document=document,
                files=files,
            )

    LegacySourceHandler.__name__ = f"LegacyHandler[{plugin_name}]"
    LegacySourceHandler.__qualname__ = LegacySourceHandler.__name__
    return LegacySourceHandler


def wrap_legacy_plugins() -> dict[str, type[SourceHandler]]:
    """Wrap all legacy importer/downloader plugins in source handlers.

    :returns: the wrapped handler classes keyed by plugin name.
    """
    from papis.downloaders import DOWNLOADERS_EXTENSION_NAME
    from papis.importer import IMPORTER_NAMESPACE_NAME, Importer
    from papis.plugin import get_plugins

    handlers: dict[str, type[SourceHandler]] = {}
    for namespace in (IMPORTER_NAMESPACE_NAME, DOWNLOADERS_EXTENSION_NAME):
        for name, cls in get_plugins(namespace).items():
            if name in handlers:
                logger.warning(
                    "Ignoring legacy plugin '%s' from namespace '%s': "
                    "name already used by an earlier plugin.",
                    name,
                    namespace,
                )
                continue

            if not (isinstance(cls, type) and issubclass(cls, Importer)):
                logger.warning(
                    "Ignoring legacy plugin '%s' from namespace '%s': "
                    "not an Importer subclass.",
                    name,
                    namespace,
                )
                continue

            handlers[name] = wrap_legacy_plugin(name, cls)

    return handlers
