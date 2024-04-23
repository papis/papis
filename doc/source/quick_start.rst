Quick start
===========

In this quick start, we'll create a library, then download a couple documents
with PDFs, open, tag and organise the files.  To do that, we'll use the Papis
program with all its commands.  You can list the available commands executing
``papis``, and get help with any of these commands with ``papis COMMAND
--help``, where ``COMMAND`` is the command you want to know more about.

Creating a new library
----------------------

We will illustrate the process by creating a first library with a couple of
``pdf`` documents in it.  While you can manually create and edit the configuration file, we can use a wizard.  For that, we'll execute the command

.. code:: bash

    papis init

It will prompt us for some settings, like the name of the library, where to
place it, which programs to use to edit and open files, etc.  None of the
settings are irreversible, so feel free to accept the defaults and edit them
after getting used to the program.

After following the wizard, it's important that you manually create the folder
that will store the library.  The default location in Linux is the ``papers``
directory under the system-defined document path (usually ``$HOME/Documents``).


Adding the first document
-------------------------

Now we'll add the first article to the library.  There are several ways to
do so, like automatically fetching a PDF file along with its metadata from a
website, or manually using an existing file.  Let's start with the automatic
method, which will download an `example article from arXiv <https://arxiv.org/
abs/2404.14339>`, show the file as downloaded, and then automatically add to
the library:

.. code:: bash

    papis add --from arxiv https://arxiv.org/abs/2404.14339

This uses the ``add`` command, which can fetch a PDF from a local file or also
from some supported websites thanks to downloaders, specialized functions of
Papis that visit a website, download the document and its metadata.  There are
several available downloaders, listed, for instance in ``papis add --help``
and ``papis list --downloaders``.  In this example, we've used the `` `arxiv``
downloader, and we've supplied it with the full URL to the article.

If Papis doesn't provide a downloader for the website you normally use, you
can manually download a PDF from there.  Here we'll illustrate this workflow,
assumming we download the PDF of `Isaac Newton's Principia Mathematica <https://
www.gutenberg.org/files/28233/28233-pdf.pdf>` and then tell Papis about the file
and some of its information:

.. code:: bash

    papis add 28233-pdf.pdf --set author "Isaac Newton" --set title "Principia Mathematica"

Let us see how this works exactly.  In the example above we have used the flag
``--set`` to manually attribute the ``author`` and ``title`` to the document.
You can see all the possible flags for the command ``add`` if you use the
``help`` flag:

.. code:: bash

  papis add --help


Listing documents
-----------------

In both automatic and manual ``add`` methods above, Papis copied the
``document.pdf`` file into a folder inside the library.  To know where it stored
the files, you can use the ``papis list`` program, with an optional query to
filter the database.  Following the examples above, we can thus issue

.. code:: bash

    papis list

to list all the files on the database, or

.. code:: bash

    papis list author:newton

to list only the documents that have author metadata containing ``newton``.  You can supply other filters.  To know which fields you can filter, visit the :ref:info.yaml article to learn more about the document information model.  We'll use one of the built-in fields, ``title``:

.. code:: bash

    papis list title:principia

These commands will output the document locations within a database, and these
can be visited to open the PDF files.  Papis also provides facilities to avoid
manually going to this folders, as we'll see in the following section.


Opening documents
-----------------

Now that we have a couple of documents, we can execute the command

.. code:: bash

    papis open

Papis will now ask us which document we want to open.  Use the arrow keys to
navigate within this interface, or type some text to filter the list.  Papis
then will narrow down the list to those entries that contain the text you
entered.  An alternative way would be to supply the command with the query, just
like in the example before:

.. code:: bash

    papis open author:newton

In this case, if we only have a document, Papis will directly open it, without
making us pick from a list.


Tagging the documents
---------------------

Now that you have a starter library, it's easy to find any document at a
glance.  But, as soon as the library starts growing, you might want to tag the
documents so that they are easier to reach, group, export, or organise. Papis
doesn't impose a tag hierarchy or schema, so you are free to use the tags
that make sense for your workflow. For instance, you could use tags that match
the keywords of those documents, whether you've read the document, publishing
status, etc.

To put this into practice, let's add the tag ``physics`` to the documents by
author Isaac Newton, ie. matching the query ``author:"Isaac Newton"``:

.. code:: bash

  papis tag --append physics author:"Isaac Newton"


And now, let's assume we want to keep these documents handy for citing within our next project.  We could add the tag "project" to them using the command

.. code:: bash

  papis tag --append project author:"Isaac Newton"


Organising the library
----------------------

While it is possible to mostly avoid opening the actual document files, you
might want to ensure the library folders and files are organised to your
liking.  For this purpose, Papis offers some commands that help you with this.
``rename`` changes the name of the folders, and ``mv`` modifies the nesting of
the folders.

To illustrate this, we'll imagine we've imported a document, but the metadata
was wrong, so we've edited that using ``papis edit``.  To make the folder name
reflect the changes, it's enough to just run ``papis rename`` and pick the
relevant document.

To organise the library so that it nests the documents by year, for example, you
can use the ``papis mv --folder-name "{doc[year]}"``, then pick the documents
you want to apply this operation to.


Exporting documents
-------------------

After adding and organising the documents in the library, exporting their
information to a BibTex file or any other supported format becomes very similar
to opening or tagging them.  To export, for instance, all documents from the
library to a file called ``project.tex``, we can use the command

.. code:: bash

    papis export --all --output project.tex

To export part of the library, for instance, only those documents that contain
the tag "project", the command becomes

.. code:: bash

    papis export --all --output project.text tags:project


Sample workflow
---------------

Let's tie this up with an example workflow that utilizes ``add``, ``export``,
``open```, and introduces some other commmands.  We'll imagine we are now
starting from a blank slate, and that we have to deliver a short thesis on the
computational linguistics topic of coreference resolution, and experiments on
that, and we only have one reference, from an anthology.

This anthology has some reference, one of which is Hobbs (1979).  We'll search
Google Scholar for the reference "hobs 1979".  We get a result from the Wiley
Online Library.  Since this is an open access document, we can give Papis the
DOI of the document:

.. code:: bash

    papis add --from doi https://doi.org/10.1207/s15516709cog0301_4

Papis has downloaded the information for the document, but, from the output,
you'll notice that the actual PDF file couldn't be downloaded.  Turns out, the
document is freely downloadable, but the publisher wants us using a browser to
download this file.  This can be solved by downloading the file and using the
``addto`` Papis command, which attaches files to documents.  Assuming the file
has been downloaded to ``/tmp/document.pdf``, the next command would be

.. code:: bash

    papis addto -f /tmp/document.pdf hobbs

This command will also be helpful to also add all those documents downloader
after logging into a paywall.  Now, We can open the PDF to start researching the
topic, using

.. code:: bash

    papis open hobbs

and take notes with

.. code:: bash

    papis edit --notes hobbs

After these two commands, we'll take notes of the document.  For instance, we
see some definitions of the topic that have good examples, so we can just have a
some bullet points in the notes.  These can include the page numbers where they
are located, for later reference:

.. code::

    - introductions, p 3
    - definitions, p. 5
    - coherence relations, p. 6
    - bridge with traditional linguistics, p. 7
    ... and so on ...

    - Linguists have identified various relations connecting text units, often without formal definitions. p. 20
    ... and so on...

Once we're done with this article, we could find one that cites it.  Again, we
could use a tool such as Semantic Scholar or Google Scholar.  We've found one
that cites Hobbs (1979) and that has some experiments with LLMs.  We'll repeat
the steps before, now with the URL of the desired document:

.. code:: bash

    papis add https://aclanthology.org/P19-1442.pdf

Papis may now prompt which downloader to use, to which we can reply with ``all``
or the number of the matching document.  The rest of the steps will be the same
as before.

After repeating the steps as desired, we could now start writing our
deliverable, using the notes and the documents as reference.  To cite
articles, for instance, we could use the facilities in our text editor if it
has integration with Papis (such as nvim), or with BibTex after exporting the
``bib`` file.
