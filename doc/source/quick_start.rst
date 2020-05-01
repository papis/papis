
Quick start
===========

This is a tutorial that should be enough to get you started using papis.  Papis
tries to be as simple and lightweight as possible, therefore its document model
should be too as simple as possible.

But before taking a look at its database structure let us show the daily
usage of papis for a regular user. This tutorial is command-line based, so you
should be familiar with opening a terminal window on your system and
do some general operations with it, like creating folders and files.

Creating a new library
----------------------

We will illustrate the process by creating a first library with a couple of
``pdf`` documents in it. Papis can be highly configured using configuration
files. Many programs use configuration files maybe without you being aware of
it. Papis' configuration files are stored together inside the folder

::

    ~/.config/papis

Bear in mind that ``~`` means "Home Directory". Inside this directory a
configuration file is found,

::

    ~/.config/papis/config

Right now we will open this file for editing and we will create a library.  In
papis everything should be human-readable and human-editable. So adding a
library is as easy as adding two lines to this configuration file.

Say that you want to create a "papers" library, where you can finally order
all those pdf's hanging around on your computer. We create this library
by putting these two lines inside the config file:

.. code:: ini

    [papers]
    dir = ~/Documents/mypapers

In the above lines we have created a library with the name ``papers`` which is
located in the directory ``~/Documents/mypapers``.  So all the documents that
we will be adding to the library will be located inside
``~/Documents/mypapers``, and nowhere else. Everything that papis needs to take
care of your ``papers`` library is inside the ``~/Documents/mypapers`` directory,
self-contained.

If you have not already, add the two lines to the ``~/.config/papis/config``
file and save it, and we will proceed to add some documents.
Of course, you have to make sure that the folder ``~/Documents/mypapers``
exists, so go ahead and create it

::

    mkdir -p ~/Documents/mypapers


Adding the first document
-------------------------

If you don't have any special pdf lying around let me choose one for you:
`link <https://www.gutenberg.org/files/28233/28233-pdf.pdf?session_id=8cecccb488f337378d5826ba1f31984f612f7ff5/>`_.
You can download this document and we are going to add it into the ``papers``
library.

Assuming that you have the document in the current directory and you have renamed
the document to ``document.pdf``, do the following to add the pdf into your
library:

.. code:: bash

  papis add document.pdf --set author "Newton" --set title "Principia Mathematica"

And it's done! We have added our first book to the library.

Let us see how this works exactly. Papis consists of many commands, and one of
these commands is ``add``. ``add`` itself has many flags, which are options for the
given command. In the example above we have used the flags ``author`` and
``title`` to tell papis to use ``Newton`` as the author's name and ``Principia
Mathematica`` as the document's title. You can see all the possible flags
for the command ``add`` if you use the ``help`` flag, i.e., if you issue the
following command

.. code:: bash

  papis add --help

Now you are asking yourself, what happened to the pdf-file? Where is it
stored?  Is it stored in an obscure database somewhere in my computer? No,
papis just copied the ``document.pdf`` file into a folder inside the library
folder ``~/Documents/papers/``. If you now go there, you will see that a folder
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

and the document should open in your default pdf-viewer.
You can change the default pdf-viewer in your configuration file
(see section on :ref:`configuration-file`).

Now you can try to repeat the same process with another pdf-file lying around.
When you hit ``papis open`` again, it will ask you which one you want.
If you input parts of the title or the author's name it will try to match
what you typed with the paper you are looking for, so that you can get the
desired paper very easily.


.. comment
  .. raw:: html

    <script type="text/javascript"
      src="https://asciinema.org/a/hrNaFMh4XwqVpWsGWDi5SASUC.js"
      id="asciicast-hrNaFMh4XwqVpWsGWDi5SASUC" async>
    </script>

Of course papis shines really in other areas, for instance imagine
you are browsing this paper
`prl paper <https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.124.171801/>`_
and you want to add it to your library, as of version ``v0.9``
you can issue one of these commands

::

  papis add https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.124.171801/
  papis add --from url https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.124.171801/
  papis add --from doi 10.1103/PhysRevLett.124.171801/

Here you can see it in action using the smart matching first alternative

.. raw:: html

    <script type="text/javascript"
      src="https://asciinema.org/a/i2kXyZMNaT8n7YRz7DcVIfqm5.js"
      id="asciicast-i2kXyZMNaT8n7YRz7DcVIfqm5" async>
    </script>

