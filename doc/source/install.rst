Installation
============

.. image:: https://badge.fury.io/py/papis.svg
    :target: https://badge.fury.io/py/papis

.. image:: https://repology.org/badge/vertical-allrepos/papis.svg
    :target: https://repology.org/project/papis/versions

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

- The package `papis` is also found in the archlinux repositories
  `here <https://aur.archlinux.org/packages/papis/>`__.
- If you want to use the git version of ``papis`` instead
  refer to `papis-git <https://aur.archlinux.org/packages/papis-git/>`__ package.
  Thanks `Julian <https://julianhauser.com/>`__!.

NixOS
-----

If you are running `NixOS <https://nixos.org/>`__ or you have the
`nix <https://github.com/NixOS/nix>`__ package manager installed, you can install
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


Guix
----

.. note::

    At this moment there are no recipes for Papis in the main Guix repositories.
    If such a recipe is added, it is recommended to install from the official
    sources.

If you are running the `Guix System <https://guix.gnu.org/>`__ or you have the
`guix <https://guix.gnu.org/>`__ package manager installed and you would like
to install ``papis`` the 'Guix way', you can use the included recipe from
:download:`python-papis.scm <../../contrib/python-papis.scm>`. This recipe can
be downloaded locally and installed using

.. code:: sh

    guix package --install-from-file=python-papis.scm

This Guix recipe was made by running the following command

.. code:: sh

  guix import pypi papis@0.13 --recursive

manually fixing some dependencies and switching off some failing tests so
that the package could be build with Guix. This can be used for newer versions
until an official recipe in the main Guix repositories is published.

From source
-----------

First of all you have to get the code, open a terminal and hit

::

  git clone https://github.com/papis/papis.git

or download the
`zip file <https://github.com/papis/papis/archive/refs/heads/main.zip>`__.


Go inside of the ``papis`` source folder and you can install it with ``python3``.

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


Running tests
-------------

In order to run the necessary tests to submit a pull request,
make sure that the following commands pass


::

  python -m pytest papis/ tests/ --cov=papis
  python -m mypy papis
  python -m flake8 papis

for it, make sure that you have ``pytest``, ``flake8`` and ``mypy``
installed.

You can make sure that you have everything you need to run the tests
by doing in the root directory

::

   pip install .[develop]

this command installs the necessary dependencies for developing
and running the tests. Look inside of the file ``setup.py`` for
further information.

You can also look at the folder ``tools`` for scripts used in the
CI testing phase for further context.
