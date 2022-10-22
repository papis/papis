Git
===

Papis is conceived to work well with the tool `git`, this would also work with
`mercurial <https://www.mercurial-scm.org/>`__
or `subversion <https://subversion.apache.org/>`__.

Here you will find a description of a possible workflow using git with papis.
This is not the only workflow, but it is the most obvious.

Let's say you have a library named ``books`` in the directory
``~/Documents/MyNiceBooks``. You could turn the ``books`` library into
a `git` repository, just doing for example

::

  papis -l books run git init

or just going to the library directory and running the command there:

::

  cd ~/Documents/MyNiceBooks
  git init

Now you can add everything you have in the library with ``git add .``
if you are in the library's directory or

::

  papis -l books git add .

if you want to do it using the `papis`' ``git`` command.

Interplay with other commands
-----------------------------

Some papis commands give you the opportunity of using ``git`` to manage
changes. For instance, if you are adding a new document, you could use
the ``--commit`` flag to also add a commit into your library, so if you do

::

  papis add --set author "Pedrito" --set title "Super book" book.pdf --commit

then also papis will do an automatic commit for the book, so that you can
push your library afterwards to a remote repository.

You can imagine that papis commands like ``rename`` and ``mv`` should also
offer such functionality, and they indeed do through the ``--git`` flag.
Go to their documentation for more information.

Updating the library
--------------------

You can use papis' simple ``git`` wrapper,

::

  papis git pull

Usual workflow
--------------

Usually the workflow is like this:

When adding a document that you know for sure you want in your library:

  - Add the document and commit it, either by ``git add --commit``
    or committing the document after adding it to the library.

  - Pull changes from the remote library, maybe you pushed something
    at work (reference changes etc..) and you do not have it yet there,
    you would do something like

    ::

      papis git pull

  - Push what you just added

    ::

      papis git push

  - Review the status of the library

    ::

      papis git status

When editing a document's info file:

  - Edit the file and then take a look at the ``diff``

    ::

      papis git diff

  - Add the changes

    ::

      papis git add --all

  - Commit

    ::

      papis git commit

  - Pull/push:

    ::

      papis git pull
      papis git push

Of course these workflows are just very basic examples.
Your optimal workflow could look completely different.
