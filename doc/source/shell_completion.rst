Shell autocompletion
====================

Papis has a bash autocompletion script that comes installed
when you install papis with ``pip3``.

It should be installed in a relative path

::

  PREFIX/etc/bash_completion.d/papis

normally the ``PREFIX`` part is ``/usr/local/``, so you can add the
following line to your ``~/.bashrc`` file

::

  source /usr/local/etc/bash_completion.d/papis

or get the bash script from
`here <https://raw.githubusercontent.com/alejandrogallo/papis/master/scripts/shell_completion/click/papis.sh/>`_.


Zsh
---

There is also a way for ``zsh`` users to autocomplete. Either downloading the
script
`here <https://raw.githubusercontent.com/alejandrogallo/papis/master/scripts/shell_completion/click/papis.zsh/>`_.
or adding the following line int the ``.zshrc`` configuration file

::

  eval "$(_PAPIS_COMPLETE=source_zsh papis)"
