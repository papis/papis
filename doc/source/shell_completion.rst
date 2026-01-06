Shell completion
================

Papis has shell completion for ``bash``, ``fish`` and ``zsh`` through the
`click framework <https://click.palletsprojects.com/en/latest/shell-completion/#shell-completion>`__
that comes with it when installed through ``pip``. To control the directory
in which the completions get installed, use the environment variables:

.. code:: bash

    PAPIS_<SHELL>_COMPLETION_DIR=my/custom/directory

where ``<SHELL>`` is the uppercase name of the shell (e.g. ``BASH``) and the
paths are considered subdirectories of the chosen prefix. The default paths for
each shell are given below.

* ``bash``: the completion script is installed in
  ``$PREFIX/share/bash-completion/completions`` and works directly with
  the `bash-completion <https://github.com/scop/bash-completion>`__ package.
  It can also be sourced manually using (or added to your ``.bashrc``):

    .. code:: bash

        source $PREFIX/share/bash-completion/completions/papis.bash

* ``fish``: the completion script is installed in
  ``$PREFIX/share/fish/vendor_completions.d``, which should be sourced
  automatically (see the
  `fish docs <https://fishshell.com/docs/current/completions.html#where-to-put-completions>`__
  for more details). It can also be sourced manually using (or added to your
  ``config.fish``):

    .. code:: bash

        source $PREFIX/share/fish/vendor_completions.d/papis.fish

* ``zsh``: the completion script is installed in ``$PREFIX/share/zsh/site-functions``,
  which is sourced automatically starting with version ``5.0.7`` (see the
  `zsh docs <https://zsh.sourceforge.io/Doc/Release/Completion-System.html>`__
  for more details). It can also be sourced manually using (or added to your
  ``.zshrc``):

    .. code:: bash

        source $PREFIX/share/zsh/site-functions/_papis

Alternatively, the completion can be generated on-the-fly by running (see more in the
`click docs <https://click.palletsprojects.com/en/latest/shell-completion/#shell-completion>`__):

.. code:: bash

   eval "$(_PAPIS_COMPLETE=<shell>_source papis)"

where ``<shell>`` is one of the shells supported by ``click``. Note that older
versions of ``click`` used ``source_<shell>`` instead for the values of
``_PAPIS_COMPLETE``.


Document completions
--------------------

Commands that expect a document query (``edit``, ``addto``, etc.) support
document completions. These are mainly controlled by the :confval:`completion-format`
configuration setting and can be be triggered on e.g.

.. code:: bash

   papis edit ein<TAB>

Normally, all documents that match the *incomplete* query via :confval:`match-format`
are returned and the user can filter them further using the shell's capabilities.

To force the results to only include matches that have the *incomplete* query as a
prefix, use :confval:`prefix-only-completions`. For example, ``zsh`` automatically
replaces the *incomplete* string with the longest common prefix of the suggested
completions, which can break your workflow. To prevent losing the incomplete string,
enable :confval:`prefix-only-completions`.

Note that the document completion only sets the value of
:confval:`completion-format` for the selected document as the query. This can
still bring up the Papis picker if the selection is not sufficiently unique.
