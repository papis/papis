Papis
=====

|PyPI-Versions| |Build_Status| |build_appveyor| |Coveralls| |RTD| |Pypi|
|Code_Quality| |zenodo_badge| |PyPI-Downloads| |MYPY-CHECKED|

|Packaging_status|

Description
-----------

Papis is a powerful and highly extensible command-line based document
and bibliography manager.

|quickstartsvg|

Learn more:

- Take a look at the `documentation <http://papis.readthedocs.io/en/latest/>`__!
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
   `papis-zotero <https://github.com/papis/papis-zotero>_`.
-  Create custom scripts to help you achieve great tasks easily
   (`doc <http://papis.readthedocs.io/en/latest/scripting.html>`__).
-  Export documents into many formats (bibtex, yaml..)
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
    papis add --from-doi 10.1090/noti963 --set tags programming rnoti-p434.pdf

Now open one for example, or edit them

::

    papis open
    papis edit

|superquickstartsvg1| Or edit them and export them to bibtex

::

    papis export --all --bibtex > mylib.bib

|superquickstartsvg2|

find help messages in all commands:

::

    papis -h
    papis add -h

AND MUCH, MUCH MORE!

Authors
-------

See the ``AUTHORS`` list for a list of authored commits.

.. |zenodo_badge| image:: https://zenodo.org/badge/82691622.svg
   :target: https://zenodo.org/badge/latestdoi/82691622
.. |superquickstartsvg1| image:: https://papis.github.io/images/superquickstart1.svg
.. |superquickstartsvg2| image:: https://papis.github.io/images/superquickstart2.svg
.. |quickstartsvg| image:: https://papis.github.io/images/quick.svg
.. |Pypi| image:: https://badge.fury.io/py/papis.svg
   :target: https://badge.fury.io/py/papis
.. |RTD| image:: https://readthedocs.org/projects/papis/badge/?version=latest
   :target: http://papis.readthedocs.io/en/latest/?badge=latest
.. |Coveralls| image:: https://coveralls.io/repos/github/papis/papis/badge.svg?branch=master
   :target: https://coveralls.io/github/papis/papis?branch=master
.. |Build_Status| image:: https://travis-ci.org/papis/papis.svg?branch=master
   :target: https://travis-ci.org/papis/papis
.. |build_appveyor| image:: https://ci.appveyor.com/api/projects/status/ncklsgj2xep5fqwx/branch/master?svg=true
   :target: https://ci.appveyor.com/project/alejandrogallo/papis/branch/master
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


Related software
----------------

Here is a list of similar software:

- `Mendeley <https://www.mendeley.com/>`__ Proprietary.
- `Zotero <https://www.zotero.org/>`__ FOSS
- `Xapers <https://finestructure.net/xapers/>`__.
- `pubs <https://github.com/pubs/pubs/>`__.
