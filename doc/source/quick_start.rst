
Quick start
===========

This is a tutorial that should be enough to get you started using papis.  Papis
tries to be as simple and lightweight as possible, therefore its database
structure is ridiculously simple.

But before taking a look at its database structure let us see how is the daily
usage of papis for a regular user. This tutorial is command-line based, so you
should be familiar with opening a terminal window in your system.

Creating a new library
----------------------

We will illustrate the process by creating a first library with a couple of
```pdf``` documents in it. Papis can be highly configured using configuration
files. Many programs use configuration files without you maybe being aware of
it. Papis' configuration files are stored together inside the folder

::

    ~/.papis

Bear in mind that ``~`` means "Home Directory". Inside this directory a
configuration file is found,

::

    ~/.papis/config

Right now we will open this file to edit and we will create a library.  In
papis everything should be human-readabale and human-editable. So adding a
library is as easy as adding two lines to this configuration file.

Say that you want to create a "papers" library, where you can finally order
all those pdf's hanging around in your computer. We can create this library
by putting inside the config file the two lines:

.. code:: ini

    [papers]
    dir = ~/Documents/mypapers

In the above lines we have created a library with the name ``papers`` which is
located in the directory ``~/Documents/mypapers``.  So all the documents that
we will be adding to the library will be located inside
``~/Documents/mypapers``, and nowhere else. Everything that papis needs to take
care of your papers library is inside the ``~/Documents/mypapers`` directory,
self-contained.

So now add the two lines to the ``~/.papis/config`` file and save it, and we will
proceed to add some documents.


Adding the first document
-------------------------

If you don't have any special pdf lying around let me choose one for you:
`PDF <https://www.gutenberg.org/files/28233/28233-pdf.pdf?session_id=8cecccb488f337378d5826ba1f31984f612f7ff5/>`_.
You can download this document and we are going to add it into the papers
library.

Supposing that you have the document in the current directory and you have renamed
the document to ``document.pdf``, you can do the following to add this into your
library:

.. code:: bash

  papis add document.pdf --author "Newton" --title "Principia Mathematica"

And it's done! We have added our first book to the library.

Let us see how this works exactly. Papis consists of many commands, and one of
these commands is ``add``. Add itself has many flags, which are options for the
given command. In the example above we have used the flags ``author`` and
``title`` to tell papis to use ``Newton`` as the author name and ``Principia
Mathematica`` as the title of the document. You can see all the posible flags
for the command ``add`` if you use the ``--help`` flag, i.e., if you issue the
following command

.. code:: bash

  papis add --help

Now you are asking yourself, what happened with the pdf file? Where it is
stored?  Is it stored in an obscure database somewhere in my computer? No,
papis just copied the ``document.pdf`` file into a folder inside the library
folder ``~/Documents/papers/``. If you go now there, you will see that a folder
with a weird name has been created. Inside of the folder there is the
``document.pdf`` file and another file, ``info.yaml``.

If you open the ``info.yaml`` file you will see the following contents:

.. code:: yaml

  author: Newton
  title: Principia Mathematica
  files:
  - document.pdf

This file is all that papis uses to store the information of your newly added
document. It is stored in a nicely readable `yaml
<https://en.wikipedia.org/wiki/YAML/>`_ format.

Now you already have your first document, and.. you can open it!
Just do

::

  papis open

and the document should just open in your default pdf viewer.
You can change the default pdf viewer in your configuration file
(see section on :ref:`configuration-file`).


Nice Reading!!

