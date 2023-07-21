Hooks
=====

From version ``0.12`` papis has a minimal hook infrastructure.
Some parts of papis define and run hooks so that users
and plugin writers can also tap into this functionality.

A hook is declared in the same way as a plugin, in fact
they are implemented in the same way within the
`stevedore <https://github.com/openstack/stevedore>`__ plugin.

1 Writing hooks as a user
-------------------------

Right now the only way to add a hook as a user is using your
``config.py`` configuration file, which gets loaded
when your papis configuration gets loaded.

As an example you can add a function to the ``on_edit_done``
hook like

.. code:: python

    import papis.hooks

    papis.hooks.add("on_edit_done", lambda: print(42))

2 Writing hooks as a developer
------------------------------

To add a hook as a plugin writer or a developer you can just add the *entrypoint*
to the ``pyproject.toml`` file. For instance for the ``on_edit_done`` hook you
would write

.. code:: toml

    [project.entry-points."papis.hook.on_edit_done"]
    my_hook_name = "path.module:function"
