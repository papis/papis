"""The lookup flow of the source-handler system.

Lookup returns data for a single document.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING
from urllib.parse import urlsplit

from papis.sources.dispatch import SourceResult, attempt, resolve_handlers

if TYPE_CHECKING:
    from collections.abc import Sequence

    from papis.document import DocumentLike
    from papis.sources.handler import (
        FileReference,
        Followup,
        LookupInput,
        SourceHandler,
    )


@dataclass
class LookupResult(SourceResult):
    """The lookup flow's outcome for single handler.

    :param document: the document metadata found.
    :param files: references to files to attach to the document.
    :param followup: a request for further evidence.
    """

    document: DocumentLike | None = None
    files: list[FileReference] = field(default_factory=list)
    followup: Followup | None = None


def run_handler(
    handler: type[SourceHandler],
    evidence: LookupInput,
) -> LookupResult:
    """Match and look up one source handler and build its result record.

    :param handler: the handler to run.
    :param evidence: the evidence for matching and lookup.
    :returns: the outcome lookup result.
    """
    instance, error = attempt(handler.name, handler.match_for_lookup, evidence)
    if error is not None:
        return LookupResult(
            source=handler.name,
            priority=handler.priority,
            status="match_failed",
            message=error,
        )

    if instance is None:
        return LookupResult(
            source=handler.name,
            priority=handler.priority,
            status="no_match",
        )

    output, error = attempt(handler.name, instance.lookup, evidence)
    if error is not None or output is None:
        return LookupResult(
            source=handler.name,
            priority=handler.priority,
            status="failed",
            message=error,
        )

    got_result = bool(output.document or output.files or output.followup)
    return LookupResult(
        source=handler.name,
        priority=handler.priority,
        status="ok" if got_result else "no_result",
        document=output.document,
        files=list(output.files),
        followup=output.followup,
        message=output.message,
    )


def lookup(
    evidence: LookupInput,
    *,
    sources: Sequence[str] | None = None,
) -> list[LookupResult]:
    """Lookup a single document with the registered source handlers.

    :param evidence: the facts from which to match and lookup.
    :param sources: restrict lookup to these sources.
    :returns: the list of results (one per resolved handler), sorted by priority.
    :raises ValueError: if there's no evidence or handler name is unknown.
    """
    if not (evidence.input or evidence.content or any(evidence.fields.values())):
        raise ValueError("lookup requires an input string, content, or metadata fields")

    # NOTE: for local file paths, we only use the basename for match/lookup.
    scheme = urlsplit(evidence.input).scheme.lower()
    if evidence.kind == "file" and scheme not in {"http", "https"}:
        evidence = replace(
            evidence, input=os.path.splitext(os.path.basename(evidence.input))[0]
        )

    results: list[LookupResult] = []

    for handler in resolve_handlers(sources, capability="lookup"):
        results.append(run_handler(handler, evidence))

    results.sort(key=lambda result: result.priority)

    return results
