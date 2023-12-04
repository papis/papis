.. _git-support:

Git support
===========

Papis is made to work well with `git <https://git-scm.com/>`__ and has
functionality in most of its command to interact with it. This functionality
can be turned on by default by using the :ref:`config-settings-use-git`
configuration setting. This guide gives a description of a possible workflow
for using Git with Papis. This is not the only workflow, but it is the most
obvious.

Let's say you have a library named ``books`` in the directory
``~/Documents/MyNiceBooks``. You could turn the ``books`` library into
a Git repository by running

.. code:: sh

    papis -l books git init

which is completely equivalent to going into the library directory and running
the commands there

.. code:: sh

    cd ~/Documents/MyNiceBooks
    git init

As this is the first run, we can just add all the documents to the repository
(equivalent to a ``git add .`` and a ``git commit -m '...'``)

.. code:: sh

    papis -l books git add .
    papis -l books git commit -m 'initial commit'

In general the ``papis git`` command will just forward any arguments directly
to the underlying ``git`` command. This allows users to easily access any Git
functionality.

Interplay with other commands
-----------------------------

.. warning::

   Only the ``papis git`` command can be used to initialize a Git repository.
   All other commands assume the repository exists in the directory of the
   current library and their Git functionality will fail otherwise.

Some papis commands give you the opportunity of using Git to manage
changes. For instance, if you are adding a new document, you could use
the ``--git`` flag to also commit the document into Git like this

.. code:: sh

    papis add --git --set author 'Pedrito' --set title 'Super book' book.pdf

In this case, Papis will do an automatic add + commit for the document. After
that, you can push your library to a remote repository by running

.. code:: sh

   papis git push origin main

As expected, other Papis commands like ``update``, ``addto``, ``rename``, ``mv``,
etc. also offer such functionality, and they all go through the ``--git`` flag.

Updating the library
--------------------

To update the library from a remote repository, you can simply run

.. code:: sh

    papis git pull

Usual workflow
--------------

With all this in mind, assuming the you have a ``git`` repository set up in
the library folder, a ``papis git`` workflow could be based on the following.

When adding a document that you know for sure you want in your library:

1. Add the document and commit it, either by ``papis add --git``
   or by using ``papis git add`` after adding it to the library.

2. Pull changes from the remote repository, maybe you pushed something
   on another machine (reference changes, etc.) and you do not have it on
   you current machine. You would do something like

    .. code:: sh

        papis git pull

3. Push what you just added

    .. code:: sh

        papis git push

4. Review the status of the library

    .. code:: sh

        papis git status


When editing a document's info file:

1. Edit the file and then take a look at the ``diff``

    .. code:: sh

        papis git diff

2. Add the changes to the staging area

    .. code:: sh

        papis git add --all

3. Commit the changes

    .. code:: sh

        papis git commit

4. Push your changes.

Of course these workflows are just very basic examples. Your optimal workflow
could look completely different.
