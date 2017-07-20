
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
`PDF <https://www.gutenberg.org/files/28233/28233-pdf.pdf?session_id=8cecccb488f337378d5826ba1f31984f612f7ff5/>`_



you can then work with the library by doing

::

    papis -l library-name open

and so on...


You have installed everything, then you can do

::

    papis -h

To see the help, the first time that papis is run it will create a
configuration folder and a configuration file in

::

    ~/.papis/config

There you will have already a library called papers defined with
directory path ``~/Documents/papers/``. Therefore in principle you could
now do the following:

::

    papis -v add --from-url https://arxiv.org/abs/1211.1036

And this will download the paper in ``https://arxiv.org/abs/1211.1036``
and also copy the relevant information of its bibliography.

You can know more about each command doing

::

    papis -h
    papis add -h

etc..

