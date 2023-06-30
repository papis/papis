Plugin architecture
===================

General architecture
--------------------

Papis uses the `stevedore <https://github.com/openstack/stevedore/>`__ library
for general plugin management. However, other modules are not expected to
interact with it and instead use the helper wrappers given by ``papis.plugin``.

The different plugins in papis (e.g. ``papis.command``, ``papis.exporter`` etc.)
define a so-called :class:`~stevedore.extension.ExtensionManager`, which loads various
objects that have been declared as
`entrypoints <https://packaging.python.org/en/latest/specifications/entry-points/>`__
(plugins) in the package
`metadata <https://packaging.python.org/en/latest/guides/creating-and-discovering-plugins/>`__.

For example, the ``yaml`` exporter in ``papis.yaml`` is defined as

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
            "papis.exporter": [
                ...
                "yaml=papis.yaml:exporter",
                ...
            ],
        ...
    )

where ``yaml`` is the name of the entrypoint, ``papis.yaml`` is the module
in which it is located and ``exporter`` is the callable used to invoke the
plugin, i.e. the format is ``<name>=<module>:<callable>``. The exporter can be
retrieved by name using

.. code:: python

    import papis.plugin

    extension_manager = papis.plugin.get_extension_manager("papis.exporter")
    yaml_exporter = extension_manager["yaml"].plugin

    yaml_string = yaml_exporter(mydocs)

Due to the entrypoint mechanism used by ``stevedore``, any third-party package
can add plugins to papis in this fashion. More information about each type of
plugin available in papis is given below.

Exporter
--------
TO DOCUMENT

Command
-------
TO DOCUMENT

Importer
--------
TO DOCUMENT

Explore
-------
TO DOCUMENT
