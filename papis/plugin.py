from typing import List, Dict, Any

from stevedore import ExtensionManager

import papis.logging

logger = papis.logging.get_logger(__name__)

MANAGERS: Dict[str, ExtensionManager] = {}


def stevedore_error_handler(manager: ExtensionManager,
                            entrypoint: str, exception: str) -> None:
    logger.error("Error while loading entrypoint '%s': %s.", entrypoint, exception)


def get_extension_manager(namespace: str) -> ExtensionManager:
    """
    :arg namespace: the namespace for the entry points.
    :returns: an extension manager for the given entry point namespace.
    """
    manager = MANAGERS.get(namespace)
    if manager is None:
        logger.debug("Creating manager for namespace '%s'.", namespace)

        manager = ExtensionManager(
            namespace=namespace,
            invoke_on_load=False,
            verify_requirements=True,
            propagate_map_exceptions=True,
            on_load_failure_callback=stevedore_error_handler
        )

        MANAGERS[namespace] = manager

    return manager


def get_available_entrypoints(namespace: str) -> List[str]:
    """
    :returns: a list of all available entry points in the given *namespace*
        sorted alphabetically.
    """
    manager = get_extension_manager(namespace)
    return sorted(str(e) for e in manager.entry_points_names())


def get_available_plugins(namespace: str) -> List[Any]:
    """
    :returns: a list of all available plugins in the given *namespace*.
    """
    return [e.plugin for e in get_extension_manager(namespace)]
