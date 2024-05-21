Quick guide
===========

In this quick guide, we'll create a library, download a couple documents, and
then work on them by opening, tagging, updating, exporting, and organising them.
In doing so, you will be introduced to the ``papis`` command and number of its
subcommands. These subcommands (which we'll simply call "commands" from now on)
are run with ``papis COMMAND`` (where ``COMMAND`` is the command you want). To
get a list of all commands, simply run ``papis --help``. If you want to get help
with a specific command, check out ``papis COMMAND --help``.

Creating a new library
----------------------

You can't manage a library without a library to manage, and so the first thing
we will do is create one! You could do this manually by editing the
:ref:`configuration file <configuration-file>`, but there's a command that will
help you get going:

.. code:: bash

    papis init

This command will prompt you for some settings, such as the name and location of
the library, which programs to use to open files, and so on. All of the settings
can be changed by editing the configuration file, so feel free to accept the
defaults for the time being and fine-tune them once you have become familiar
with Papis.

Adding the first documents
--------------------------

Let's populate our library next. There are several ways to add a document to
your library: you can automatically fetch a document's metadata along with a PDF
or add the document manually. Adding documents is done with the ``papis add``
command.

Let's start with the automatic method. We will download an example article from
arXiv: <https://arxiv.org/abs/2404.14339>`. The command will download all the
data, show the downloaded file, and then (after asking for confirmation)
automatically add it to the library:

.. code:: bash

    papis add --from arxiv https://arxiv.org/abs/2404.14339

We have invoked ``papis add`` with the ``--from arxiv`` option, which specifies
the ``arxiv`` *importer*. Papis contains various importers, which allow it to
get data from a variety of online sources. Finally, we provide the arXiv URL of
the document in which we're interested. You can take a look at all the other
available importers with ``papis list --importers``.

If Papis is missing an importer for some website, you may need to manually
download the PDF and enter the metadata yourself. We'll illustrate this by
downloading the PDF of Isaac Newton's Principia Mathematica and then adding the
file along with some basic metadata:

.. code:: bash

    wget https://www.gutenberg.org/files/28233/28233-pdf.pdf -O principia.pdf
    papis add principia.pdf --set author "Isaac Newton" \
    --set title "Principia Mathematica"

First, we download the file with ``wget``. We then run ``papis add`` with the
filename as the first argument and two instances of the ``--set`` option to
manually set the ``author`` and ``title`` (the ``papis add`` command is split
over two lines with ``\`` just so it displays better in this guide).

Finally, a situation that is unfortunately familiar to most: papers behind
paywalls. The importer might be able to get the metadata automatically but fail
at fetching the PDF. In this case, you might have to get the file yourself. You
can use a slightly modified ``papis add`` command if you then want to create an
entry in your library.

.. code:: bash

    wget https://www.unicode.org/L2/L2017/17407-frowning-poo.pdf
    papis add 17407-frowning-poo.pdf \
    --from doi https://doi.org/10.1007/s11192-017-2554-0

First, we're downloading a PDF about the Unicode frowning poop emoji as
a substitute for the paywalled paper that you'd have downloaded yourself. We
then use ``papis add`` with the ``doi`` importer, which downloads metadata based
on an article's ``doi`` identifier (from `Crossref
<https://www.crossref.org/>`__).

Adding files
------------

You can also add files to existing documents in your library. This can be useful
in various situations. For instance, you might have tried to add a document, but
Papis couldn't download the relevant file. You then find the file elsewhere and
want to add it to the existing document. Or maybe you'd like to add both the PDF
and EPUB version of some file to a document. Just to show how this works, let's
add the frowning poop emoji PDF once more to the same document (so that we end
up with two PDFs attached to it):

.. code:: bash

    papis addto --files 17407-frowning-poo.pdf mikki

The path specified after ``--files`` tells Papis where to find the file. Papis
will attach the file to the document that matches the query "mikki" or open the
picker if there are multiple matching documents.

Listing documents
-----------------

All the documents you add end up in folders inside your library. To find out
where exactly a specific file is, use the ``papis list`` command.

.. code:: bash

    papis list

Here, Papis will open the picker listing all the files in the library. You can
further narrow down the results by typing your query. Alternatively, you can use
the arrow keys to select the entry you're interested in. You can also use
``ctrl-t`` to select multiple entries. Pressing ``Enter`` will leave the picker
and print the paths to the selected documents.

As usual, you can optionally provide a query to filter the database:

.. code:: bash

    papis list newton

Here, Papis will list only the documents whose metadata matches "newton".
Because there is only one such document, Papis skips the picker and directly
provides you with the path.

If you want to filter in a more specific manner, for instance by a document's
title, you can use the following:

.. code:: bash

    papis list title:principia

Instead of by "title", you can filter by any other field stored in the Papis
library. The :ref:`info.yaml section <info-file>` gives an overview of these
fields.

Opening documents
-----------------

Using ``papis list`` to find a document's path to manually open a file gets old
quickly. That's why Papis also provides facilities to open documents directly.
We can open a document with:

.. code:: bash

    papis open

This will work similarly to ``papis list``. If there are multiple matches, Papis
opens the picker, and if there is only a single match, the picker is skipped.
However, unlike ``papis list``, ``papis open`` doesn't print the path to the
document, but opens the attached file.

You can narrow down your query just as in ``papis list``:

.. code:: bash

    papis open newton

Adding notes
------------

You opened the Principia Mathematica and started reading. Now you want to jot
down some notes so that you can review them later. Papis has built-in
functionality for this:

.. code:: bash

    papis edit --notes newton

We called ``papis edit`` with the ``--notes`` flag, which tells Papis that we
want to edit the note file (or create one if it doesn't yet exist). We need to
specify ``--notes`` because ``papis edit`` will otherwise open the `info.yaml
file <info-file>` where Papis stores the document's metadata. The command ends
with the query "newton", which we use to select the document in which we're
interested.

Tagging the documents
---------------------

As your library grows, you might want to add tags to keep things organised and
searchable. For instance, you could create tags with your documents' keywords,
note whether you've read the document, keep track of publishing status, and so
on.

Let's say you want to add the tag "physics" to all documents by Isaac Newton:

.. code:: bash

    papis tag --append physics newton

Or maybe, you want to tag the documents used in a specific project. We could add
the tag "project apple" to them using the command

.. code:: bash

    papis tag --append "project apple" newton

Because our tag has white space in it, we had to surround it with ``"``.

Updating documents
------------------

You realise that you want to adjust the metadata of the Principia Mathematica
document in our library. While "Isaac Newton" is indeed the guy's name, you'd
like to be more polite and include his title and rename the author to "Sir Isaac
Newton". While the ``papis tag`` command we've discussed previously is
specialised for editing tags, the ``papis update`` command can be used to change
metadata more generally. We can use it to easily rename the author:

.. code:: bash

    papis update --set author "Sir Isaac Newton" newton

The structure of the command might be familiar to you by now. First, we use
``--set author "Sir Isaac Newton"`` to tell ``papis update`` to set the author
to what we want, and then we add a query to identify the document we're
interested in.

Exporting documents
-------------------

You're likely using some other piece of software to write text with proper
referencing and bibliographies. The most widely supported file format used for
these purposes is BibTeX. You can export your Papis library to BibTeX, so that
you can then use it elsewhere.

To export all documents in the library to a BibTeX file called ``all.bib``, you
can use the command:

.. code:: bash

    papis export --all --output all.bib

Note the use of the ``--all`` flag. This tells Papis that you want to run the
command with all files that match the query. In this case, it means that ``papis
export`` creates a ``.bib`` file based on all documents in the library. Without
the ``--all`` flag, Papis would instead have opened the picker (as it did in
previous examples where we didn't use this flag), allowing you to select the
document.

To export only a part of the library, for instance all documents that contain
the tag "project", you can add a query:

.. code:: bash

    papis export --all --output project_apple.bib tags:"project apple"

Renaming folders
----------------

Papis will automatically name the folders in your library in a reasonable (and
configurable) way, but if you want to rename them manually, you're free to do
so. For this purpose, Papis offers the ``rename`` command, which changes the
name of a document's folder.

This can be particularly useful when you've adjusted some document's metadata
and would like the folder's name to reflect this. Remember how we changed the
author of the Principia Mathematica from "Isaac Newton" to "Sir Isaac Newton"?
Let's make that show up in the folder name! It's simple to do this: run ``papis
rename``, pick the relevant document, and follow the prompts. Here, you do not
need to set anything by hand as Papis regenerates the folder name based on the
updated metadata.

Alternatively, you could also use the ``--folder-name`` option to set the folder
name to whatever you want. Finally, you could also adjust the
:confval:`add-folder-name` configuration option so that folders are
automatically named according to your preferences.

Starting over
-------------

You should now know about Papis' basics and be able to use it to organise your
library. If you want to start over and add your own documents, you may want to
delete the files we've added in this quick guide. You will need to delete the
Papis configuration folder and the library you've created when running ``papis
init``. This resets everything, so that by running ``papis init`` again, you'll
start anew.

If you're unsure about the location of the library we've created for this quick
guide, run the following command.

.. code:: bash

    papis config --section papis dir

The ``papis config`` command can tell you about the state of the Papis
configuration. Here, we're asking it to give us the value of the option ``dir``
in the section ``papis``. If you've changed the name of the library when running
``papis init`` you will need to change the section name to your library's name.
You can now use ``rm -r`` or your file browser to delete this folder.

The Papis configuration folder's location depends on your operating system. You
can find out where it is by running:

.. code:: bash

    papis list --paths

The folder you'll need to the delete is the one called ``PAPIS_CONFIG_FOLDER``.
