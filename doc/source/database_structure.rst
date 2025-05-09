The database
============

One of the things that makes Papis interesting is the fact that
there can be many backends for the database system, including no database.

Right now there are three types of databases that the user can use:

- No database:
    ::

      database-backend = papis
      use-cache = False

- Simple cache based database:
    ::

      database-backend = papis

- `Whoosh <https://whoosh.readthedocs.io/en/latest>`__  based database:
    ::

      database-backend = whoosh

If you just plan to have up to 3000 documents in your library,
you will have ample performance with the two first options.
However if you're reaching higher numbers,
you'll probably want to use the ``Whoosh`` backend for very good performance.

You can select a database by using the flag :confval:`database-backend`.

Papis database
--------------

Without a database, Papis would need to crawl through the library folders and see
which subfolders have an ``info.yaml`` file. Repeatedly accessing the filesystem
like this can be slow on older computers, remotely mounted partitions, etc.

To help with this, Papis implements a simple caching system. For each library,
it creates a database (as defined by :confval:`database-backend`) that holds
sufficient relevant information about the documents to avoid such slowdowns.

These cache files are stored per default in:

::

  ~/.cache/papis/

Notice that most ``papis`` commands will update the cache if it has to be the case.
For instance the ``edit`` command will let you edit your document's information
and after you are done editing it will update the information for the given
document in the cache.
If you go directly to the document and edit the info file without
passing through the ``papis edit`` command, the cache will not be updated and
therefore Papis will not know of these changes, although they will be there.
In such cases you will have to *clear the cache*.

Clearing the cache
^^^^^^^^^^^^^^^^^^

To clear the cache for a given library you can use the command ``cache``:

.. code::

    papis cache clear

In order to clear and rebuild the cache (i.e., reset it), you can simply run:

.. code::

    papis cache reset

Query language
^^^^^^^^^^^^^^

Since version ``v0.3``, Papis implements a query language to search documents.
Queries can contain any field of the info file, so that ``author:einstein
publisher:review`` will match documents that have ``author`` match with
``einstein`` AND ``publisher`` match with ``review``. Note that only the ``AND``
filter is implemented in this simple query language and that ``OR`` is not
supported. If you need this, consider using the `Whoosh database`_.

For illustration, here are some examples:

  - Open documents where the author key matches 'albert' (ignoring case) and
    year matches '05' (i.e. could be '1905' or '2005'):

    .. code::

      papis open 'author : albert year : 05'

  - Add the restriction to the previous search that the usual matching matches
    the substring 'licht' in addition to the previously selected:

    .. code::

      papis open 'author : albert year : 05 licht'

    This is not to be mixed with the restriction that the key `year` matches
    `'05 licht'`, which will not match any year, i.e.:

    .. code::

      papis open 'author : albert year : "05 licht"'


Disabling the cache
^^^^^^^^^^^^^^^^^^^

You can disable the cache using the configuration setting ``use-cache``
and set it to ``False``, e.g.:

.. code:: ini

  [settings]

  use-cache = False

  [books]
  # Use cache for books but don't use for the rest of libraries
  use-cache = True


Whoosh database
---------------

Papis can alternatively use the performant `Whoosh library
<https://whoosh.readthedocs.io/en/latest>`__.

Of course, the performance comes at a cost. To achieve more performance,
a database backend should create an index with information about the documents.
Parsing a user query means going to the index and matching the query to
what is found in the index. This means that the index can not in general
have all the information that the info file of the documents includes.

In other words, the Whoosh index will store only certain fields from the
documents' info files. The good news is that we can tell Papis exactly
which fields we want to index. These flags are

- :confval:`whoosh-schema-fields`
- :confval:`whoosh-schema-prototype`

The prototype is for advanced users. If you just want to, say, include
the publisher to the fields that you can search in, then you can put:

::

  whoosh-schema-fields = ['publisher']

and you will be able to find documents by their publisher.
For example, without this line set for publisher, the query:

::

  papis open publisher:*

will not return anything, since the publisher field is not being stored.


Query language
^^^^^^^^^^^^^^

The Whoosh database uses the Whoosh query language which is much more
advanced than the query language in the `Papis database`_.

The Whoosh query language supports both ``AND`` and ``OR``, for instance:

::

  papis open '(author:einstein AND year:1905) OR title:einstein'

will give papers of einstein in the year 1905 together with all papers
where einstein appears in the title.

You can read more about the Whoosh query language
`here <https://whoosh.readthedocs.io/en/latest/querylang.html>`__.
