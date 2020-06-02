"""
General architecture
--------------------

Papis uses the package
`stevedore <https://github.com/openstack/stevedore/>`_
for general plugin management.

The only papis module invoking ``stevedore`` should be
``papis/plugin.py``.

The different plugins in papis like ``papis.command``,
``papis.exporter`` etc. define a so-called ``ExtensionManager``
which loads various objects that have been declared in a python
package somewhere.

For example, the yaml exporter is defined as

.. code:: python

    def exporter(documents: List[papis.document.Document]) -> str:
        string = yaml.dump_all(
            [papis.document.to_dict(document) for document in documents],
            allow_unicode=True)
        return str(string)

and declared in ``setup.py`` as

.. code:: python

    setup(
        ...
        entry_points={
            'papis.exporter': [
                'bibtex=papis.bibtex:exporter',
                'json=papis.json:exporter',
                'yaml=papis.yaml:exporter',
            ],
        ...
    )

and the exporter can be used as in the code below

.. code:: python

    import papis.plugin
    extension_manager = papis.plugin.get_extension_manager("papis.exporter")
    # yaml_exporter is the function defined above
    yaml_exporter = extension_manager["yaml"].plugin

    yaml_string = yaml_exporter(mydocs)

Now a developer is able to write another exporter in some package
and install the package in the system.
The ``extension_manager`` will be able to access the provided functions
in the package if they have been declared in the entry points of
the ``setup.py`` script of the named package.
"""
import logging
from stevedore import ExtensionManager
from typing import List, Dict, Any  # noqa: ignore

logger = logging.getLogger("papis:plugin")


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
    return list(
        map(str, get_extension_manager(namespace).entry_points_names()))


def get_available_plugins(namespace: str) -> List[Any]:
    return [e.plugin for e in get_extension_manager(namespace)]
