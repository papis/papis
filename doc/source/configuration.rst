.. _configuration-file:

Configuration file
------------------

.. Warning::

  Coming soon...

Papis uses a configuration file in *INI* format. You can then have
several libraries which work independently from each other.

For example, maybe you want to have one library for papers and the other
for some miscellaneous documents. An example for that is given below

.. code:: ini

    [papers]
    dir = ~/Documents/papers

    [settings]
    opentool = rifle
    editor = vim
    default = papers

    [books]
    dir = ~/Documents/books
    gagp = git add . && git commit && git push origin master

