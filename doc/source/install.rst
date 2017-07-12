Installation
============

Just use the Makefile:

If you want to install it globally, just hit

::

    sudo make install-deps
    sudo make install

If you want to install it locally:

::

    make install-deps-local
    make install-local

If you want to install it locally and have the development version:

::

    make install-deps-local
    make install-dev-local

And to see the available targets hit:

::

    make help

Also you need the following packages:

::

    python3-readline
    python3-ncurses

