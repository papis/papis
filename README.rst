Papis
=====

|Build_Status| |ghbadge| |Coveralls| |RTD| |Code_Quality|
|zenodo_badge|

Description
-----------

Papis is a powerful and highly extensible command-line based document
and bibliography manager.

|quickstartsvg|

Learn more:

- Take a look at the `documentation <http://papis.readthedocs.io/en/latest/>`__!
- Blog post about getting paper's references with ``papis explore``
  `here <https://alejandrogallo.github.io/blog/posts/getting-paper-references-with-papis/>`__.
- Blog post about using papis with zotero and SyncThing
  `here <http://nicolasshu.com/zotero_and_papis.html>`__.
- GNU/Linux Switzerland wrote about papis
  `here <https://gnulinux.ch/papis-dokumentenverwaltung-fuer-die-kommandozeile>`__.
- The folks at `OSTechNix <https://www.ostechnix.com/>`__ have dedicated us a
  review, you may also check it out `here
  <https://www.ostechnix.com/papis-command-line-based-document-bibliography-manager/>`__.
- A review in Spanish is also available at `ubunlog
  <https://ubunlog.com/papis-administrador-documentos/>`__.

Main features
-------------

-  Synchronizing of documents: put your documents in some folder and
   synchronize it using the tools you love: git, dropbox, rsync,
   OwnCloud, Google Drive ... whatever.
-  Share libraries with colleagues without forcing them to open an
   account, nowhere, never.
-  Download directly paper information from *DOI* number via *Crossref*.
-  (optional) **scihub** support, use the example papis script
   ``examples/scripts/papis-scihub`` to download papers from scihub and
   add them to your library with all the relevant information, in a
   matter of seconds, also you can check the documentation
   `here <http://papis.readthedocs.io/en/latest/scihub.html>`__.
-  Import from Zotero and other managers using
   `papis-zotero <https://github.com/papis/papis-zotero>`__.
-  Create custom scripts to help you achieve great tasks easily
   (`doc <http://papis.readthedocs.io/en/latest/scripting.html>`__).
-  Export documents into many formats (bibtex, yaml, ...)
-  Command-line granularity, all the power of a library at the tip of
   your fingers.

Contributing
------------

Contributions are very welcome! Take a look at the files
``CONTRIBUTING.md`` for general rules, ``ROADMAP.md`` for possible
contribution topics and ``HACKING.md`` for additional code-related
information.

Super quick start
-----------------

Install papis with pip3

::

    sudo pip3 install papis

Let us download a couple of documents

::

    wget http://www.gnu.org/s/libc/manual/pdf/libc.pdf
    wget http://www.ams.org/notices/201304/rnoti-p434.pdf

Now add them to the (defaultly created) library, you can set
any keyword you like already when adding documents, for instance
you can set the year `--set year 2018` or tags for organizing
`--set tags programming`,

::

    papis add libc.pdf --set author "Sandra Loosemore" --set title "GNU C reference manual" --set year 2018 --set tags programming --confirm
    # Get paper information automatically via de DOI
    papis add --from doi 10.1090/noti963 --set tags programming rnoti-p434.pdf

Now open one for example, or edit them

::

    papis open
    papis edit

|superquickstartsvg1| Or edit them and export them to bibtex

::

    papis export --all --format bibtex > mylib.bib

|superquickstartsvg2|

find help messages in all commands:

::

    papis -h
    papis add -h

If you so prefer, you can also browse your papers using the web application

::

   papis serve

|webapp-einstein|

AND MUCH, MUCH MORE!

Contact
-------

Feel free to use issues, github discussions,
our `IRC libera channel <https://kiwiirc.com/client/irc.libera.chat/#papis>`__
or our `zulip channel <https://papis.zulipchat.com>`__.

Authors
-------

See the ``AUTHORS`` list for a list of authored commits.

.. |zenodo_badge| image:: https://zenodo.org/badge/82691622.svg
   :target: https://zenodo.org/badge/latestdoi/82691622
.. |superquickstartsvg1| image:: https://papis.github.io/images/superquickstart1.svg
.. |superquickstartsvg2| image:: https://papis.github.io/images/superquickstart2.svg
.. |quickstartsvg| image:: https://papis.github.io/images/quick.svg
.. |webapp-einstein| image:: https://papis.github.io/images/web-app-einstein.jpg
.. |Pypi| image:: https://badge.fury.io/py/papis.svg
   :target: https://badge.fury.io/py/papis
.. |RTD| image:: https://readthedocs.org/projects/papis/badge/?version=latest
   :target: http://papis.readthedocs.io/en/latest/?badge=latest
.. |Coveralls| image:: https://coveralls.io/repos/github/papis/papis/badge.svg?branch=master
   :target: https://coveralls.io/github/papis/papis?branch=master
.. |Build_Status| image:: https://travis-ci.org/papis/papis.svg?branch=master
   :target: https://travis-ci.org/papis/papis
.. |Packaging_status| image:: https://repology.org/badge/vertical-allrepos/papis.svg
   :target: https://repology.org/metapackage/papis
.. |Code_Quality| image:: https://img.shields.io/lgtm/grade/python/g/papis/papis.svg?logo=lgtm&logoWidth=18
   :target: https://lgtm.com/projects/g/papis/papis/context:python
.. |PyPI-Downloads| image:: https://img.shields.io/pypi/dm/papis.svg?label=pypi%20downloads&logo=python&logoColor=white
   :target: https://pypi.org/project/papis
.. |PyPI-Versions| image:: https://img.shields.io/pypi/pyversions/papis.svg?logo=python&logoColor=white
   :target: https://pypi.org/project/papis
.. |MYPY-CHECKED| image:: http://www.mypy-lang.org/static/mypy_badge.svg
   :target: http://mypy-lang.org/
.. |OpenHub| image:: https://www.openhub.net/p/papis/widgets/project_thin_badge.gif
   :target: https://www.openhub.net/p/papis
.. |Contributors| image:: https://img.shields.io/github/contributors/papis/papis
.. |ghbadge| image:: https://github.com/papis/papis/workflows/CI/badge.svg
.. |zulip| image:: https://img.shields.io/badge/papis-join_chat-brightgreen.svg
   :target: https://papis.zulipchat.com
.. |libera| image:: https://img.shields.io/badge/irc-%23papis-green
   :target: https://kiwiirc.com/client/irc.libera.chat/#papis



Related software
----------------

Here is a list of similar software:

- `Mendeley <https://www.mendeley.com/>`__ Proprietary.
- `Zotero <https://www.zotero.org/>`__ FOSS
- `Xapers <https://finestructure.net/xapers/>`__.
- `pubs <https://github.com/pubs/pubs/>`__.


Papis projects maintainers
--------------------------

If you find papis useful and want to maintain one of papis
plugins, feel free to contact us. Right now some of papis projects
and maintainers are the following

========================================================== =========================================================================================
project                                                    maintainer(s)
========================================================== =========================================================================================
`papis <https://github.com/papis/papis-rofi/>`__ (core)    `Alejandro Gallo <https://alejandrogallo.github.io/>`__ `teto <https://github.com/teto>`__ `Julian Hauser <https://github.com/jghauser>`__ `Alex Fikl <https://github.com/alexfikl>`__
`papis-rofi <https://github.com/papis/papis-rofi/>`__      `Etn40ff <https://github.com/Etn40ff>`__
`papis-dmenu <https://github.com/papis/papis-dmenu>`__     YOU?
`papis-vim <https://github.com/papis/papis-vim>`__         YOU?
`papis.nvim <https://github.com/jghauser/papis.nvim>`__    `Julian Hauser <https://github.com/jghauser>`__
`papis-emacs <https://github.com/papis/papis.el>`__        `alejandrogallo <https://alejandrogallo.github.io/>`__
`papis-zotero <https://github.com/papis/papis-zotero>`__   `lennonhill <https://github.com/lennonhill>`__
`papis-libgen <https://github.com/papis/papis-zotero>`__   YOU?
`papis-firefox <https://github.com/papis/papis-firefox>`__ `wavefrontshaping <https://github.com/wavefrontshaping>`__
========================================================== =========================================================================================
