Papis
=====

|Build Status|
|Coveralls|
|Packaging status|

Description
-----------

Papis is a powerful and highly extensible command-line based document
and bibliography manager.

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
-  Import from Zotero and other managers using the script in
   ``examples/scripts/papis-zotero``
   (`doc <http://papis.readthedocs.io/en/latest/importing.html>`__).
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

Now add them to the (defaultly created) library

::

    papis add libc.pdf --author "Sandra Loosemore" --title "GNU C reference manual" --confirm
    # Get paper information automatically via de DOI
    papis add --from-doi 10.1090/noti963 rnoti-p434.pdf

Now open one for example

::

    papis open

|asciicast| Or edit them and export them to bibtex

::

    papis edit
    papis export --all --bibtex > mylib.bib

|asciicast|

find help messages in all commands:

::

    papis -h
    papis add -h

|asciicast| AND MUCH, MUCH MORE!

Authors
-------

See the ``AUTHORS`` list for a list of authored commits.

.. |Coveralls| image:: https://coveralls.io/repos/github/papis/papis/badge.svg?branch=master
   :target: https://coveralls.io/github/papis/papis?branch=master
.. |Build Status| image:: https://travis-ci.org/papis/papis.svg?branch=master
   :target: https://travis-ci.org/papis/papis
.. |Packaging status| image:: https://repology.org/badge/vertical-allrepos/papis.svg
   :target: https://repology.org/metapackage/papis
.. |asciicast| image:: https://asciinema.org/a/oEHU9oPlGrKPOQzGMxvqkh5Fe.png
   :target: https://asciinema.org/a/oEHU9oPlGrKPOQzGMxvqkh5Fe
.. |asciicast| image:: https://asciinema.org/a/QrUntd87K97hoKowxkAb4AYZ0.png
   :target: https://asciinema.org/a/QrUntd87K97hoKowxkAb4AYZ0
.. |asciicast| image:: https://asciinema.org/a/48Dv1rfX44yjJD6Sbc71gpXGr.png
   :target: https://asciinema.org/a/48Dv1rfX44yjJD6Sbc71gpXGr
