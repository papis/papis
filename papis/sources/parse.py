"""The parse flow of the source-handler system.

Parsing converts metadata from some format to Papis documents.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import papis.logging
from papis.sources.dispatch import SourceResult, attempt, resolve_handlers

if TYPE_CHECKING:
    from collections.abc import Sequence

    from papis.document import DocumentLike
    from papis.sources.handler import ParseInput

logger = papis.logging.get_logger(__name__)


@dataclass
class ParseResult(SourceResult):
    """The parse flow's outcome for a single handler.

    :param documents: the documents the handler answered with.
    """

    documents: list[DocumentLike] = field(default_factory=list)


def parse(
    parse_input: ParseInput, *, sources: Sequence[str] | None = None
) -> list[ParseResult]:
    """Parse the content of *parse_input* into Papis documents.

    :param parse_input: the content to parse into documents.
    :param sources: constrain parsing to these source handlers.
    :raises ValueError: if *parse_input* has no content or *sources* contains an unknown
        handler.
    """
    content = parse_input.content
    if not content:
        raise ValueError("parse requires content")

    handlers = resolve_handlers(sources, capability="parse")

    results: list[ParseResult] = []
    for handler in handlers:
        if "parse" not in handler.capabilities:
            results.append(
                ParseResult(
                    source=handler.name,
                    priority=handler.priority,
                    status="no_match",
                    message="source does not support parse",
                )
            )
            continue

        output, error = attempt(handler.name, handler.parse, content)
        if error is not None:
            results.append(
                ParseResult(
                    source=handler.name,
                    priority=handler.priority,
                    status="failed",
                    message=error,
                )
            )
            continue

        if output is None:
            results.append(
                ParseResult(
                    source=handler.name, priority=handler.priority, status="no_match"
                )
            )
            continue

        results.append(
            ParseResult(
                source=handler.name,
                priority=handler.priority,
                status="ok" if output.documents else "no_result",
                documents=output.documents,
                message=output.message,
            )
        )

    return results
