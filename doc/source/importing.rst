Importing from bibtex files
===========================

Many users will want to import a library from a bibtex file
that another program such as ``zotero``, ``mendeley`` or
``jabref`` will have exported. These programs usually have a
field called ``FILE`` or ``file`` that points to a path
where the document file can be found.

To import such a library you can use a script originally
intended for ``zotero`` but that is general enought to work
for other programs too.

To install this script you can copy the file ``papis-zotero`` in the
repository's example directory to your papis ``config/scripts`` directory.

You can do this automatically issuing the following commands

.. code:: bash

  wget -O ~/.config/papis/scripts/papis-zotero https://raw.githubusercontent.com/alejandrogallo/papis/master/examples/scripts/papis-zotero
  chmod +x ~/.config/papis/scripts/papis-zotero

Now the zotero script is accessible from papis:

.. code:: bash

  papis zotero -h

If you have a bibtex somewhere in your computer, you can use the script:

.. code:: bash

  papis zotero library.bib

.. warning::

  Note that if your bibtex file has some pdf entries, i.e., looks like:

  .. code:: bibtex

    @article{Einstein1905Photon,
      author = { A. Einstein },
      doi = { 10.1002/andp.19053220607 },
      journal = { Ann. Phys. },
      pages = { 132--148 },
      title = { Über einen die Erzeugung und Verwandlung des Lichtes betreffenden heuristischen Gesichtspunkt },
      FILE = { path/to/some/relative/file.pdf },
      volume = { 322 },
      year = { 1905 },
    }

  then ``papis-zotero`` will interpret the path of the ``FILE`` entry
  as a relative path, so you should run the command where this relative path
  makes sense.
