"""Shared dispatch machinery for lookup, search and parse."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, ParamSpec, TypeVar

import papis.logging
from papis.exceptions import SourceError

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from papis.sources.handler import Capability, SourceHandler

logger = papis.logging.get_logger(__name__)

_T = TypeVar("_T")
_P = ParamSpec("_P")


def resolve_handlers(
    sources: Sequence[str] | None,
    *,
    capability: Capability,
) -> list[type[SourceHandler]]:
    """Resolve which source handlers should process a request.

    :param sources: explicitly requested handler names, or ``None`` for all.
    :param capability: the capability the request needs.
    :raises ValueError: if *sources* contains an unknown handler name.
    """
    from papis.sources.handler import registry

    if sources is None:
        return [handler for handler in registry if capability in handler.capabilities]

    handlers: list[type[SourceHandler]] = []
    for name in sources:
        handler = registry.get(name)
        if handler is None:
            raise ValueError(f"unknown source '{name}'")
        handlers.append(handler)

    return handlers


def attempt(
    source: str,
    fn: Callable[_P, _T],
    /,
    *args: _P.args,
    **kwargs: _P.kwargs,
) -> tuple[_T | None, str | None]:
    """Run a handler call, converting its exceptions into an error message.

    Individual source handlers' errors shouldn't crash Papis so that other source
    handlers of the same run can still complete successfully.

    :param source: name of the handler being called.
    :param fn: the handler method to call with *args* and *kwargs*.
    :returns: ``(value, None)`` on success and ``(None, error)`` on failure.
    """
    # handler methods always have '__name__'.
    action = fn.__name__  # ty: ignore[unresolved-attribute]
    try:
        return fn(*args, **kwargs), None
    except SourceError as exc:
        logger.debug("Source '%s' failed to %s.", source, action, exc_info=exc)
        return None, str(exc)
    except Exception as exc:
        logger.error(
            "Source '%s' failed to %s unexpectedly.", source, action, exc_info=exc
        )
        message = f"{type(exc).__name__}: {exc}" if str(exc) else type(exc).__name__
        return None, message


#: Status of running a source handler:
#:
#: - ``"ok"``: the handler ran and produced something,
#: - ``"no_result"``: the handler ran but produced nothing,
#: - ``"no_match"``: the handler could not work with the given evidence,
#: - ``"match_failed"``: the ``match`` step raised,
#: - ``"failed"``: the handler raised.
Status = Literal["ok", "no_match", "no_result", "match_failed", "failed"]


@dataclass
class SourceResult:
    """The shared form of an outcome for one handler run.

    :param source: name of the handler the outcome is attributed to.
    :param priority: the handler's merge priority.
    :param status: the status of the run.
    :param message: elaboration of :attr:`status`.
    """

    source: str
    priority: int
    status: Status
    message: str | None = None
