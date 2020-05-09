Installation
============

.. image:: https://badge.fury.io/py/papis.svg
   :target: https://badge.fury.io/py/papis
.. image:: https://repology.org/badge/vertical-allrepos/papis.svg
   :target: https://repology.org/metapackage/papis

Using pip
---------

The easiest way of installing papis is using the ``PyPi`` repositories and
the package manager ``pip3``, just open a terminal and type in

::

  pip3 install papis

If you are on GNU/Linux like systems you might need to type ``sudo``

::

  sudo pip3 install papis

or if you prefer installing it locally then simply type

::

  pip3 install --user papis

You can also **update** papis with ``pip``

::

  pip3 install --upgrade papis


Archlinux
---------

The package `papis` is also found in the archlinux repositories
`here <https://aur.archlinux.org/packages/papis/>`_.

NixOS
-----

If you are running `NixOS <https://nixos.org/>`_ or you have the
`nix <https://nixos.org/nix/>`_ package manager installed, you can install
papis by running:

::

  nix-env -i papis

If you like papis, just clone the repository

::

  git clone git@github.com:papis/papis.git
  cd papis

and start hacking it with:

::

  nix-shell --expr 'with import <nixpkgs> {}; papis.overrideDerivation (drv: { src = ./.; })'

This command will provide you a shell with all the dependencies required.


From source
-----------

First of all you have to get the code, open a terminal and hit

::

  git clone https://github.com/alejandrogallo/papis.git

or download the
`zip file <https://github.com/alejandrogallo/papis/archive/master.zip>`_.


Go inside of the ``papis`` source folder and you can either use the ``Makefile``
or install it with ``python3``.

The general command that you have to hit is by using the ``setup.py`` script:

.. code:: python

  python3 setup.py install


Again, if you want to install it locally because you don't have administrative
rights on your computer you simply type

.. code:: python

  python3 setup.py install --user

If you want to work on the code, you can alternatively hit

.. code:: python

  python3 setup.py develop --user


.. warning::

  If you install the package locally, the program ``papis`` will be installed
  by default into your ``~/.local/bin`` directory, so that you will have to
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

    python3-setuptools

However if you have a general enough python distribution they should be
installed.
