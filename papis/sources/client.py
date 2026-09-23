"""Client source handlers and common client machinery.

Unlike typical source handlers, client source handlers match using client state (a
folder path, a library name), read the local client state, and may be interactive.
"""

from __future__ import annotations

import os
import pathlib
from dataclasses import replace
from typing import TYPE_CHECKING

import papis.logging
from papis.exceptions import InvalidLibraryError, SourceError
from papis.sources.handler import (
    FileReference,
    LookupInput,
    LookupOutput,
    SearchInput,
    SearchOutput,
    SourceHandler,
)
from papis.sources.lookup import LookupResult, lookup, run_handler
from papis.sources.search import (
    DEFAULT_MAX_RESULTS,
    SearchResult,
    run_handler as run_search_handler,
    search,
)

if TYPE_CHECKING:
    import logging
    from collections.abc import Collection, Sequence
    from typing import Any

    from papis.document import DocumentLike
    from papis.sources.dispatch import SourceResult, Status
    from papis.sources.handler import Capability

logger = papis.logging.get_logger(__name__)


class FolderClientHandler(SourceHandler):
    """Retrieve a document from a Papis document folder."""

    name = "folder"

    @classmethod
    def match_for_lookup(cls, evidence: LookupInput) -> FolderClientHandler | None:
        return cls() if os.path.isdir(evidence.input) else None

    def lookup(self, evidence: LookupInput) -> LookupOutput:
        item = evidence.input

        from papis.document import from_folder, is_document_folder, to_dict

        if not is_document_folder(pathlib.Path(item)):
            raise ValueError(f"unknown document folder '{item}'")

        self.logger.info("Importing from folder '%s'.", item)

        from papis.id import ID_KEY_NAME

        # NOTE: the stored ID is dropped, so that it gets regenerated for the new
        # document
        doc = from_folder(item)
        doc.pop(ID_KEY_NAME, None)

        data = to_dict(doc)
        data.pop("files", None)

        return LookupOutput(
            document=data or None,
            files=[FileReference(path=path) for path in doc.get_files()],
        )


class LibraryClientHandler(SourceHandler):
    """Retrieve documents from a Papis library."""

    name = "lib"
    search_fields = ("library",)

    @classmethod
    def match_for_lookup(cls, evidence: LookupInput) -> LibraryClientHandler | None:
        from papis.config import get_lib_from_name

        try:
            get_lib_from_name(evidence.input)
        except InvalidLibraryError:
            return None
        return cls()

    def lookup(self, evidence: LookupInput) -> LookupOutput:
        item = evidence.input

        from papis.api import get_all_documents_in_lib
        from papis.pick import pick_doc

        self.logger.debug("Picking a document from library '%s'.", item)

        try:
            documents = get_all_documents_in_lib(item)
        except InvalidLibraryError:
            raise ValueError(f"unknown library '{item}'") from None

        # NOTE: Here, the user is prompted, making this source handler interactive
        docs = pick_doc(documents)
        if not docs:
            return LookupOutput()

        folder = docs[0].get_main_folder()
        if folder is None:
            return LookupOutput()

        return FolderClientHandler().lookup(LookupInput(input=folder))

    @classmethod
    def search(
        cls,
        query: SearchInput,
        *,
        max_results: int,
    ) -> SearchOutput:
        from papis.config import get_lib_name, getstring
        from papis.database import get_database

        libraries = query.filters.get("library", []) or [get_lib_name()]

        search_query = query.input or getstring("default-query-string")

        documents: list[DocumentLike] = []
        for library_name in libraries:
            try:
                db = get_database(library_name=library_name)
            except InvalidLibraryError:
                raise SourceError(f"unknown library '{library_name}'") from None

            documents.extend(db.query(search_query))

        return SearchOutput(documents=documents[:max_results])


CLIENT_HANDLERS: list[type[SourceHandler]] = [
    FolderClientHandler,
    LibraryClientHandler,
]


def get_known_sources(
    *,
    capability: Capability | None = None,
) -> list[type[SourceHandler]]:
    """Get known source handlers, sorted by name.

    :param capability: only return handlers that support this capability.
    """
    from papis.sources.handler import registry

    handlers = {cls.name: cls for cls in (*registry, *CLIENT_HANDLERS)}.values()
    return sorted(
        (cls for cls in handlers
         if capability is None or capability in cls.capabilities),
        key=lambda cls: cls.name,
    )


def lookup_followups(results: Sequence[LookupResult]) -> list[LookupResult]:
    """Look up the followups of one request's results and merge them back in.

    :param results: one request's results.
    :returns: the results with followups merged in.
    """
    from papis.gather import fetch_metadata_content

    completed: list[LookupResult] = []
    for result in results:
        followup = result.followup
        if followup is None:
            completed.append(result)
            continue

        content = fetch_metadata_content(followup.url)
        if content is None:
            messages = [result.message, f"Could not fetch followup '{followup.url}'."]
            message = "; ".join(message for message in messages if message) or None
            completed.append(
                replace(
                    result,
                    followup=None,
                    status=result.status if result.document else "failed",
                    message=message,
                )
            )
            continue

        (followup_data,) = lookup(
            LookupInput(input=followup.url, kind="file", content=content),
            sources=[followup.format],
        )
        followup_data = replace(followup_data, priority=followup.priority)

        data, _ = merge(
            sorted((result, followup_data), key=lambda item: item.priority),
        )
        document = data or None
        if document is not None:
            status: Status = "ok"
        elif followup_data.status in {"failed", "match_failed", "no_match"}:
            status = "failed"
        else:
            status = "no_result"

        messages = [result.message, followup_data.message]
        message = "; ".join(message for message in messages if message) or None
        completed.append(
            replace(
                result,
                document=document,
                files=[*result.files, *followup_data.files],
                followup=None,
                status=status,
                message=message,
            )
        )

    return sorted(completed, key=lambda result: result.priority)


def merge(
    results: Sequence[LookupResult],
    *,
    base: DocumentLike | None = None,
    pick: bool = False,
    resolve_fields: bool = False,
) -> tuple[dict[str, Any], list[FileReference]]:
    """Merge multiple results' documents into a single document.

    Later documents in list order win conflicts.

    :param results: the source result documents to merge, with later documents winning.
    :param base: pre-existing data to start from.
    :param pick: let the user select and order the results.
    :param resolve_fields: let the user interactively resolve field conflicts.
    :returns: the merged data and accumulated file references.
    """
    ordered: Sequence[LookupResult] = results
    if pick:
        candidate_results: list[LookupResult] = []
        files_only_results: list[LookupResult] = []
        for result in results:
            if result.document:
                candidate_results.append(result)
            else:
                files_only_results.append(result)

        if len(candidate_results) > 1:
            from papis.tui.utils import select_range

            options = []
            for result in candidate_results:
                from papis.document import describe

                options.append(
                    f"[{result.source}] {describe(result.document or {})} "
                    f"(files: {str(len(result.files)) if result.files else 'none'})")

            indices = select_range(
                options,
                "Select and order the sources to merge (later wins), "
                "e.g. 0, 2, 3-10, a, all")
            ordered = [
                *[candidate_results[index] for index in dict.fromkeys(indices)],
                *files_only_results,
            ]

    from papis.utils import update_doc_from_data_interactively

    data = dict(base or {})
    files: list[FileReference] = []

    for result in ordered:
        document = result.document
        if document:
            incoming = dict(document)
            incoming.pop("ref", None)

            if resolve_fields and data:
                update_doc_from_data_interactively(data, incoming, result.source)
            elif incoming:
                data.update(incoming)

        if result.files:
            files.extend(result.files)

    return data, files


def _split_sources(
    sources: Collection[str],
    capability: Capability,
) -> tuple[list[type[SourceHandler]], list[str] | None]:
    """Split requested source names into client handlers and standard names.

    :param sources: the requested source names, or an empty collection for all.
    :param capability: the capability the request needs.
    :returns: the client handlers to run and the standard source names to forward.
    """
    if not sources:
        return (
            [cls for cls in CLIENT_HANDLERS if capability in cls.capabilities],
            None,
        )

    client_handlers: list[type[SourceHandler]] = []
    standard_sources: list[str] = []
    for name in sources:
        client_handler = next(
            (cls for cls in CLIENT_HANDLERS if cls.name == name), None
        )
        if client_handler is not None:
            client_handlers.append(client_handler)
        else:
            standard_sources.append(name)

    return client_handlers, standard_sources


def lookup_item(
    evidence: LookupInput,
    sources: Collection[str] = (),
) -> list[LookupResult]:
    """Look up a single item's evidence.

    :param evidence: the gathered evidence.
    :param sources: constrain lookup to these sources.
    :returns: the results in precedence order.
    :raises ValueError: for unknown source names and empty evidence.
    """
    if not (evidence.input or evidence.content or any(evidence.fields.values())):
        raise ValueError(
            "lookup_item requires an input string, content, or metadata fields"
        )

    client_handlers, standard_sources = _split_sources(sources, "lookup")

    client_results: list[LookupResult] = []
    for handler in client_handlers:
        result = run_handler(handler, evidence)
        # NOTE: a non-matching client source shouldn't be logged when not requested.
        if sources or result.status != "no_match":
            client_results.append(result)

    standard_results = lookup_followups(lookup(evidence, sources=standard_sources))

    return sorted(standard_results + client_results, key=lambda result: result.priority)


def search_item(
    query: SearchInput,
    sources: Collection[str] = (),
    *,
    max_results: int = DEFAULT_MAX_RESULTS,
) -> list[SearchResult]:
    """Search using a single query.

    :param query: the query to search with.
    :param sources: constrain search to these sources.
    :param max_results: maximum number of results per source.
    :returns: the results in resolution order.
    :raises ValueError: for unknown source names and empty query.
    """
    if not (query.input or any(query.filters.values())):
        raise ValueError("search requires a query or at least one filter")

    client_handlers, standard_sources = _split_sources(sources, "search")

    client_results = [
        run_search_handler(handler, query, max_results=max_results)
        for handler in client_handlers
    ]
    standard_results = search(query, sources=standard_sources, max_results=max_results)

    if not sources:
        return [*standard_results, *client_results]

    results = {result.source: result for result in [*standard_results, *client_results]}
    return [results[name] for name in sources]


def log_source_result(
        logger: logging.Logger,
        result: SourceResult,
        *,
        sources: Collection[str] | None = None) -> None:
    """Log a single source result.

    :param logger: the logger to write to.
    :param result: the source handler result to log.
    :param sources: the names of the sources explicitly requested, or ``None``.
    """
    if result.status == "match_failed":
        logger.warning(
            "Source '%s' failed to match: %s",
            result.source,
            result.message or "internal error",
        )
    elif result.status == "failed":
        logger.warning(
            "Source '%s' failed: %s",
            result.source,
            result.message or "internal error",
        )
    elif result.status == "no_match":
        if sources is not None and result.source in sources:
            text = result.message or "did not match the given input"
            logger.warning("Source '%s': %s", result.source, text)
    elif result.status == "no_result":
        logger.warning("Source '%s' returned no results.", result.source)
        if result.message:
            logger.warning("Source '%s': %s", result.source, result.message)
    elif result.status == "ok":
        logger.info("Source '%s' returned a result.", result.source)
        if result.message:
            logger.warning("Source '%s': %s", result.source, result.message)
