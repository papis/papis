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
If you are running `Guix System <https://guix.gnu.org/>`__ or you have the
`guix <https://guix.gnu.org/>`__ package manager installed, you can install
papis by running:

::

  guix package --install-from-file=papis.scm

Where papis.scm file defines the papis package recipe (this is a first draft, some failing tests are switched off):

.. code:: scheme

  (use-modules
   (gnu packages)
   (gnu packages python-check)
   (gnu packages check)
   (gnu packages sphinx)
   (gnu packages openstack)
   (gnu packages python-web)
   (gnu packages python-xyz)
   (gnu packages python-build)
   (guix packages)
   (guix download)
   (guix build-system pyproject)
   (guix build-system python)
   ((guix licenses) #:prefix license:))
  
  (define python-types-tqdm
    (package
     (name "python-types-tqdm")
     (version "4.66.0.2")
     (source (origin
              (method url-fetch)
              (uri (pypi-uri "types-tqdm" version))
              (sha256
               (base32
                "0pylandfajknxprd2y06hxzfihy0cnyvh1gm3775yj0x9kjaalwm"))))
     (build-system pyproject-build-system)
     (home-page "https://github.com/python/typeshed")
     (synopsis "Typing stubs for tqdm")
     (description "Typing stubs for tqdm")
     (license #f)))
  
  (define python-types-pyyaml
    (package
     (name "python-types-pyyaml")
     (version "6.0.12.11")
     (source (origin
              (method url-fetch)
              (uri (pypi-uri "types-PyYAML" version))
              (sha256
               (base32
                "0nvpjiqf4hw5fdw3j6jh7qhxwjq8sj667viqlkdxzk98r8chnd3x"))))
     (build-system pyproject-build-system)
     (home-page "https://github.com/python/typeshed")
     (synopsis "Typing stubs for PyYAML")
     (description "Typing stubs for @code{PyYAML}")
     (license #f)))
  
  (define python-types-python-slugify
    (package
     (name "python-types-python-slugify")
     (version "8.0.0.3")
     (source (origin
              (method url-fetch)
              (uri (pypi-uri "types-python-slugify" version))
              (sha256
               (base32
                "0b2fxgf8k338h86jxwzwnjxxd576ccirh6yc5hdw00csmc86d3l6"))))
     (build-system pyproject-build-system)
     (home-page "https://github.com/python/typeshed")
     (synopsis "Typing stubs for python-slugify")
     (description "Typing stubs for python-slugify")
     (license #f)))
  
  (define python-types-pygments
    (package
     (name "python-types-pygments")
     (version "2.16.0.0")
     (source (origin
              (method url-fetch)
              (uri (pypi-uri "types-Pygments" version))
              (sha256
               (base32
                "1ch0fr7ykj64g78nqwvxkjgr7gv675p1bphcaykzwv1d9rkf94xa"))))
     (build-system pyproject-build-system)
     (propagated-inputs (list python-types-docutils python-types-setuptools))
     (home-page "https://github.com/python/typeshed")
     (synopsis "Typing stubs for Pygments")
     (description "Typing stubs for Pygments")
     (license #f)))
  
  (define python-types-html5lib
    (package
     (name "python-types-html5lib")
     (version "1.1.11.15")
     (source (origin
              (method url-fetch)
              (uri (pypi-uri "types-html5lib" version))
              (sha256
               (base32
                "14nl3dn22w8ndzy80g1rdl3kmgzz1fipvn98bkzaz8r25l3a5qc0"))))
     (build-system pyproject-build-system)
     (home-page "https://github.com/python/typeshed")
     (synopsis "Typing stubs for html5lib")
     (description "Typing stubs for html5lib")
     (license #f)))
  
  (define python-types-beautifulsoup4
    (package
     (name "python-types-beautifulsoup4")
     (version "4.12.0.6")
     (source (origin
              (method url-fetch)
              (uri (pypi-uri "types-beautifulsoup4" version))
              (sha256
               (base32
                "0iqkh67sv823df87hxbd1s8izqv77zs14dhk2rp1hh75sf2v4nh4"))))
     (build-system pyproject-build-system)
     (propagated-inputs (list python-types-html5lib))
     (home-page "https://github.com/python/typeshed")
     (synopsis "Typing stubs for beautifulsoup4")
     (description "Typing stubs for beautifulsoup4")
     (license #f)))
  
  (define python-doi
    (package
     (name "python-doi")
     (version "0.2.0")
     (source (origin
              (method url-fetch)
              (uri (pypi-uri "python-doi" version))
              (sha256
               (base32
                "16pxc7llqb14f2n5ccd88pz4sygwl51slssqm2g23g8rndpya09f"))))
     (build-system python-build-system)
     (native-inputs (list python-coverage
                          python-flake8
                          python-pep8
                          python-pytest
                          python-pytest-cov
                          python-pytest-xdist
                          python-sphinx
                          python-sphinx-autobuild
                          python-sphinx-rtd-theme
                          python-twine
                          python-wheel))
     (home-page "https://github.com/papis/python-doi")
     (synopsis "Python package to work with Document Object Identifier (doi)")
     (description
      "Python package to work with Document Object Identifier (doi)")
     (license #f)))
  
  (define python-dominate
    (package
      (name "python-dominate")
      ;; (version "2.6.0")
      ;; (version "2.7.0")
      (version "2.8.0")
      (source (origin
                (method url-fetch)
                (uri (pypi-uri "dominate" version))
                (sha256
                 (base32
                  ;; "1r71ny73ws0zf5mcml0x5yfbjhzfkn5id670zv26y2kh4gg2rv3n"
                  ;; "0jfs0n50h0q50ca3iqx1v01j9ycz6mzd6rrzap8gkswj10v020aj"
                  "01s0a2zqyni2az4wwmd8rxx9gy5ypkvrmczlf4mn33pqzazc742c"
                  ))))
      (build-system pyproject-build-system)
      (arguments '(
                   ;; #:test-backend "pytest"
                   #:tests? #f
                            ))
      (home-page "https://github.com/Knio/dominate/")
      (synopsis
       "Dominate is a Python library for creating and manipulating HTML documents using an elegant DOM API.")
      (description
       "Dominate is a Python library for creating and manipulating HTML documents using
  an elegant DOM API.")
      (license #f)))
  
  (define python-arxiv2bib
    (package
      (name "python-arxiv2bib")
      (version "1.0.8")
      (source (origin
                (method url-fetch)
                (uri (pypi-uri "arxiv2bib" version))
                (sha256
                 (base32
                  "1a27nrlcj283spgs9y07rgpwcihgkd5rclh16na6bnm4ibnhhxhk"))))
      (build-system pyproject-build-system)
      (home-page "http://nathangrigg.github.io/arxiv2bib")
      (synopsis "Get arXiv.org metadata in BibTeX format")
      (description "Get @code{arXiv.org} metadata in @code{BibTeX} format")
      (license license:bsd-3)))
  
  ;; added
  (define python-habanero
    (package
      (name "python-habanero")
      (version "1.2.3")
      (source (origin
                (method url-fetch)
                (uri (pypi-uri "habanero" version))
                (sha256
                 (base32
                  "02792xxr4mwa17khw6szmpvdlck28sz0npfw57c2rb9dnh0rwvqr"))))
      (build-system pyproject-build-system)
      (arguments '(#:tests? #f))
      (propagated-inputs (list python-requests python-tqdm))
      (native-inputs (list python-pytest))
      (home-page "https://github.com/sckott/habanero")
      (synopsis "Low Level Client for Crossref Search API")
      (description "Low Level Client for Crossref Search API")
      (license license:expat)))
  
  (package
   (name "python-papis")
   (version "0.13")
   (source (origin
            (method url-fetch)
            (uri (pypi-uri "papis" version))
            (sha256
             (base32
              "19v5r6761b0pm63xr1kxmlw7cn7cijn1dnbpbdybc6rn72lnlnpk"))))
   (build-system pyproject-build-system)
   (arguments '(#:tests? #f))
   (propagated-inputs (list python-arxiv2bib
                            python-beautifulsoup4
                            python-bibtexparser ;added
                            python-chardet
                            python-click
                            python-colorama
                            python-dominate
                            python-filetype
                            python-habanero ;added
                            python-isbnlib
                            python-prompt-toolkit
                            python-pygments
                            python-pyparsing
                            python-doi
                            python-pyyaml
                            python-requests
                            python-slugify ;added
                            python-stevedore
                            python-tqdm
                            python-typing-extensions))
   (native-inputs (list python-flake8
                        python-flake8-bugbear
                        python-flake8-quotes
                        python-mypy
                        python-pep8-naming
                        python-pylint
                        python-pytest
                        python-pytest-cov
                        python-coveralls
                        python-lsp-server
                        python-sphinx-click
                        python-sphinx-rtd-theme
                        python-types-beautifulsoup4
                        python-types-pygments
                        python-types-python-slugify
                        python-types-pyyaml
                        python-types-requests
                        python-types-tqdm))
   (home-page "https://github.com/papis/papis")
   (synopsis
    "Powerful and highly extensible command-line based document and bibliography manager")
   (description
    "Powerful and highly extensible command-line based document and bibliography
  manager")
   (license #f))
  

          

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
