from typing import List, Dict, Any, Callable  # noqa: ignore

from stevedore import ExtensionManager
import logging

import papis.plugin


logger = logging.getLogger('hooks')
NON_STEVEDORE_HOOKS = {}  # type: Dict[str, List[Callable[[Any], None]]]


def _get_namespace(name: str) -> str:
    return ("papis.hook.{}".format(name))


def get(name: str) -> ExtensionManager:
    return papis.plugin.get_extension_manager(_get_namespace(name))


def run(name: str, *args: Any, **kwargs: Any) -> None:
    full_name = _get_namespace(name)
    logger.debug("Running hooks for %s", full_name)
    for callback in papis.plugin.get_available_plugins(full_name):
        callback(*args, **kwargs)
    hooks = NON_STEVEDORE_HOOKS.get(full_name)
    if hooks:
        for callback in hooks:
            callback(*args, **kwargs)


def add(name: str, fun: Callable[[Any], None]) -> None:
    full_name = _get_namespace(name)
    logger.debug("Adding hook for %s", full_name)
    hooks = NON_STEVEDORE_HOOKS.setdefault(full_name, [])
    hooks.append(fun)
