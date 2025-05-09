.. _installation:

Installation
============

.. image:: https://badge.fury.io/py/papis.svg
    :target: https://badge.fury.io/py/papis

.. image:: https://repology.org/badge/vertical-allrepos/papis.svg
    :target: https://repology.org/project/papis/versions

Using pip
---------

The easiest way of installing Papis is using the ``PyPI`` repositories and
the ``pip`` package manager. Open a terminal and type:

.. code:: sh

    pip install papis

If you are on GNU/Linux-like systems you might need to type ``sudo`` to install
Papis globally like:

.. code:: sh

    sudo pip install papis

If you prefer installing it locally then simply type:

.. code:: sh

    pip install --user papis

You can also **update** Papis with ``pip``:

.. code:: sh

    pip install --upgrade papis


Arch Linux
----------

- The ``papis`` package is found in the Arch Linux AUR repository
  `here <https://aur.archlinux.org/packages/papis/>`__.
  Thanks to `Joshua <https://jpellis.me/>`__ for maintaining this package!
- If you want to use the git version of ``papis`` instead, you can try
  the `papis-git <https://aur.archlinux.org/packages/papis-git/>`__ package.
  Thanks to `Julian <https://julianhauser.com/>`__ for maintaining this package!

You can install either one with your favorite AUR helper, e.g.:

.. code:: sh

    yay -S papis

NixOS
-----

If you are running `NixOS <https://nixos.org/>`__ or you have the
`nix <https://github.com/NixOS/nix>`__ package manager installed, you can install
Papis by running:

.. code:: sh

    nix-env -i papis

For the development version, just clone the repository:

.. code:: sh

    git clone git@github.com:papis/papis.git
    cd papis

and start hacking it with:

.. code:: sh

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
be downloaded locally and installed using:

.. code:: sh

    guix package --install-from-file=python-papis.scm

This Guix recipe was made by running the following command:

.. code:: sh

  guix import pypi papis@0.13 --recursive

manually fixing some dependencies and switching off some failing tests so
that the package could be build with Guix. This can be used for newer versions
until an official recipe in the main Guix repositories is published.

From source
-----------

To install Papis from source, you can clone the repository using:

.. code:: sh

    git clone https://github.com/papis/papis.git

or download the
`zip file <https://github.com/papis/papis/archive/refs/heads/main.zip>`__.

Go inside of the ``papis`` source folder and you can install it in a standard
fashion. For example, using ``pip``:

.. code:: sh

    python -m pip install .

If you want to install it locally because you don't have administrative
rights on your computer you can simply type:

.. code:: sh

    python -m pip install --user .

.. warning::

    If you install the package locally, the program ``papis`` will be installed
    into your ``~/.local/bin`` directory by default. You may have to set your
    ``PATH`` accordingly to have access to it.

    One way of doing this in Bash shells (Linux, Ubuntu on Windows or Cygwin) is
    by adding the following line to your ``~/.bashrc`` file:

    .. code:: sh

        export PATH=$PATH:$HOME/.local/bin
