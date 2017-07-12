
Quick start
===========

This is a tutorial that should be enough to get you started using papis.

You have installed everything, then you can do

::

    papis -h

To see the help, the first time that papis is run it will create a
configuration folder anf a configuration file in

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

Create new library
==================

To create a new library you just simply add to the configuration file:

.. code:: ini

    #
    #  Other sutff
    #

    [library-name]
    dir = path/to/the/library/folder

    #
    #  Other sutff
    #

you can then work with the library by doing

::

    papis -l library-name open

and so on...

