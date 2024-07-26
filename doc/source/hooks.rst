Hooks
=====

From version ``0.12`` Papis has a minimal hook infrastructure.
Some parts of Papis define and run hooks so that users
and plugin writers can also tap into this functionality.

A hook is declared in the same way as a plugin, in fact
they are implemented in the same way within the
`stevedore <https://github.com/openstack/stevedore>`__ plugin.

Writing hooks as a user
-----------------------

Right now the only way to add a hook as a user is using your
``config.py`` configuration file, which gets loaded
when your Papis configuration gets loaded.

As an example you can add a function to the ``on_edit_done``
hook like

.. code:: python

    import papis.hooks

    papis.hooks.add("on_edit_done", lambda: print(42))

Writing hooks as a developer
----------------------------

To add a hook as a plugin writer or a developer you can just add the *entrypoint*
to the ``pyproject.toml`` file. For instance for the ``on_edit_done`` hook you
would write

.. code:: toml

    [project.entry-points."papis.hook.on_edit_done"]
    my_hook_name = "path.module:function"

Available hooks
---------------

``on_edit_done``
^^^^^^^^^^^^^^^^

This hook is called by ``papis edit`` after editing has finished, but before it
is saved to the database. The callbacks for this hook have the following format:

.. code:: python

    def callback(doc: papis.document.Document) -> None:
        ...

``on_add_done``
^^^^^^^^^^^^^^^

This hook is called by ``papis add`` after all editing has finished, but before
the document is searched for duplicates and added to the database. The callbacks
for this hook have the following format:

.. code:: python

    def callback(tmp_doc: papis.document.Document) -> None:
        ...

Note that the ``tmp_doc`` argument is not the final document. It will be moved to
a final location inside the chosen library after the hook was called.
