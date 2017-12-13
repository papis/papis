Installation
============

Using pip
---------

The easiest way of installing papis is using the ``PyPi`` repositories and
the package manager ``pip3``, just open a terminal and type in

::

  pip3 install papis

If you are on GNU/Linux like systems you might need to type ``sudo``

::

  sudo pip3 install papis

of if you prefer installing it locally then simply type

::

  pip3 install --user papis

You can also **update** papis with ``pip``

::

  pip3 install --upgrade papis


From source
-----------

First of all you have to get the code, open a terminal and hit

::

  git clone https://github.com/alejandrogallo/papis.git

or download the `zip file <https://github.com/alejandrogallo/papis/archive/master.zip>`_.


Go inside of the ``papis`` source folder and you can either use the ``Makefile``
or install it with ``python3``.

Using the Makefile
^^^^^^^^^^^^^^^^^^

If you want to install it globally, just hit

::

    sudo make install

If you want to install it locally:

::

    make install-local

If you want to install it locally and have the development version:

::

    make install-dev-local

And to see the available targets hit:

::

    make help

Using python3
^^^^^^^^^^^^^

The general command that you have to hit is by using the ``setup.py`` script:

.. code:: python

  python3 setup.py install


Again, if you want to install it locally because you don't have administrative rights
in your computer you can just simply type

.. code:: python

  python3 setup.py install --user

If you want to develop on the code, you can also alternatively hit

.. code:: python

  python3 setup.py develop --user


.. warning::

  If you install the package locally, the program ``papis`` will be installed
  by default into your ``~/.local/bin`` direcrtory, so that you will have to
  set your ``PATH`` accordingly.

  One way of doing this in ``bash`` shells (``Linux`` and the like, also
  ``Ubuntu`` on Windows or ``cygwin``) is by adding the following line to your
  ``~/.bashrc`` file
  ::

    export PATH=$PATH:$HOME/.local/bin


Requirements
------------

Papis needs the following packages that are sometimes not installed with the
system ``python3`` distribution

::

    python3-ncurses
    python3-setuptools

However if you have a general enough python distribution they should be installed.
