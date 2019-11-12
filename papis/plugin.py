import logging
from stevedore import ExtensionManager  # type: ignore
from typing import List, Dict

logger = logging.getLogger("plugin")


MANAGERS = dict()  # type: Dict[str, ExtensionManager]


def stevedore_error_handler(manager: ExtensionManager,
                            entrypoint: str, exception: str) -> None:
    logger.error("Error while loading entrypoint [%s]" % entrypoint)
    logger.error(exception)


def _load_extensions(namespace: str) -> None:
    global MANAGERS
    logger.debug("creating manager for {0}".format(namespace))
    MANAGERS[namespace] = ExtensionManager(
        namespace=namespace,
        invoke_on_load=False,
        verify_requirements=True,
        propagate_map_exceptions=True,
        on_load_failure_callback=stevedore_error_handler
    )


def get_extension_manager(namespace: str) -> ExtensionManager:
    global MANAGERS
    if not MANAGERS.get(namespace):
        _load_extensions(namespace)
    extension_mgr = MANAGERS[namespace]
    assert extension_mgr is not None
    return extension_mgr


def get_available_entrypoints(namespace: str) -> List[str]:
    return get_extension_manager(namespace).entry_points_names()


def get_available_plugins(namespace: str):
    return [e.plugin for e in get_extension_manager(namespace)]
