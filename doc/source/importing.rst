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

Importing from zotero sqlite file
=================================

There is also a script that decodes the
``zotero.sqlite`` sqlite file that ``zotero`` uses to manage documents
and creates papis Documents out of it.

This script will retrieve the documents from zotero (be it ``pdf`` documents
or else) and important information like tags.

.. code:: bash

  wget -O ~/.config/papis/scripts/papis-zotero-sql https://raw.githubusercontent.com/alejandrogallo/papis/master/examples/scripts/papis-zotero-sql
  chmod +x ~/.config/papis/scripts/papis-zotero-sql

Now you have to go to the directory where zotero saves all the information,
it would look something like this on linux systems:

.. code:: bash

  cd ~/.mozilla/firefox/zqb7ju1q.default/zotero

Maybe the path is slightly different, it may vary from version to version from
zotero.  In the zotero data directory there should be a file called
``zotero.sqlite`` and there might be a ``storage`` directory with
document data inside. These will be used by ``zotero-sql`` to
retrieve information and files from.

Now you can use the script as

.. code:: bash

  papis zotero-sql

This script by default will create a directory named ``Documents`` (in your
current directory) where papis documents are stored. You can add these document
by simply moving them to your library folder

.. code::

  mv Documents/*      /path/to/your/papis/library

or also by adding them through papis using the folder flag

.. code::

  papis add --from-folder Documents/ZOTERO_ID

or write a ``bash`` for loop to do it with all the converted documents

.. code::

  for folder in Documents/* ; do papis add --from-folder $folder ; done

.. warning::

  Please be aware that the database structure of zotero is version dependent
  and this script **might** not work fully with your version.
  You can check `issue #18 <https://github.com/alejandrogallo/papis/issues/18>`_
  for more information.
