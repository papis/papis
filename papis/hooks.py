from typing import List, Dict, Any, Callable, TYPE_CHECKING

import papis.plugin
import papis.logging

if TYPE_CHECKING:
    from stevedore import ExtensionManager

logger = papis.logging.get_logger(__name__)

#: All hooks should be in this namespace, e.g. ``papis.hook.on_edit_done``.
HOOKS_EXTENSION_FORMAT = "papis.hook.{name}"

#: A dictionary of hooks added with :func:`add`. These can be added in ``config.py``
#: or from other places that do not use the entrypoint framework.
CUSTOM_LOCAL_HOOKS: Dict[str, List[Callable[..., None]]] = {}


def get(name: str) -> "ExtensionManager":
    return papis.plugin.get_extension_manager(
        HOOKS_EXTENSION_FORMAT.format(name=name)
    )


def run(name: str, *args: Any, **kwargs: Any) -> None:
    """Run a hook given by its *name*.

    Additional positional and keyword arguments are passed directly to the hook.
    If it does not support these arguments, the hook will be skipped.

    Hooks are run in the following order:

    1. The hooks defined by an entry point.
    2. The hooks defined in :data:`CUSTOM_LOCAL_HOOKS`.
    """

    hook_name = HOOKS_EXTENSION_FORMAT.format(name=name)
    logger.debug("Running callbacks for hook '%s'.", hook_name)

    callbacks = papis.plugin.get_available_plugins(hook_name)
    if hook_name in CUSTOM_LOCAL_HOOKS:
        callbacks += CUSTOM_LOCAL_HOOKS[hook_name]

    for callback in callbacks:
        try:
            callback(*args, **kwargs)
        except TypeError as exc:
            logger.error("Callback '%s' for hook '%s' got unexpected arguments.",
                         callback.__name__, hook_name, exc_info=exc)
        except Exception as exc:
            logger.error("Callback '%s' for hook '%s' failed.",
                         callback.__name__, hook_name, exc_info=exc)


def add(name: str, fun: Callable[..., None]) -> None:
    """Add an additional callback to the hook given by *name*.

    Any new callbacks are appended to the list and will be applied after existing
    ones.
    """
    hook_name = HOOKS_EXTENSION_FORMAT.format(name=name)
    logger.debug("Adding callback for '%s' hook.", hook_name)

    CUSTOM_LOCAL_HOOKS.setdefault(hook_name, []).append(fun)
