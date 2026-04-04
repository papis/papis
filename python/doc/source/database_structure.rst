The database
============

Papis stores each document in its own folder inside a *library directory*, with
all metadata kept in an ``info.yaml`` file (see :doc:`library_structure` and
:doc:`info_file`). The database is a cache of that metadata: instead of reading
every ``info.yaml`` file from disk on every command, Papis builds a single index
and keeps it up to date as documents are added, edited, or removed.

To help with this, Papis implements a simple caching system. For each library,
it creates a database (as defined by :confval:`database-backend`) that holds
sufficient relevant information about the documents to avoid such slowdowns and
allow quick access and search for document metadata.

Right now, the following backends are available:

- No database:

.. code:: ini

    database-backend = papis
    use-cache = False

- Simple :mod:`pickle`-based database:

.. code:: ini

    database-backend = papis

- `Whoosh <https://whoosh.readthedocs.io/en/latest>`__  based database:

.. code:: ini

    database-backend = whoosh

- :mod:`sqlite3`-based database:

.. code:: ini

    database-backend = sqlite

If you plan to have about <1000 documents in your library, the default
``papis`` backend will offer ample performance. However, for larger
libraries, switching to the ``sqlite`` backend should work a lot better.

Using the databases
-------------------

These database files are stored by default in :func:`~papis.utils.get_cache_home`
(on Linux, this will be something like ``~/.cache/papis``). You can
put the files next to your library by using :confval:`cache-dir`::

.. code:: ini

    [papers]
    dir = /path/to/my/papers
    cache-dir = /path/to/my/papers

When switching database backends, make sure to also update the
:confval:`default-query-string` option to match. This will be used when no
query is provided to match "all" the documents. The value differs per backend:

- ``papis`` backend: ``default-query-string = .`` (the default)
- ``whoosh`` backend: ``default-query-string = *``
- ``sqlite`` backend: ``default-query-string = *``

Note that most ``papis`` commands will update the cache if they modify the document. For
example, the ``edit`` command will let you edit your document's metadata and after you
are done editing it will update the information for the given document in the cache.

.. note::

    The cache is built automatically the first time you run any ``papis`` command
    against a library. You do not need to initialize it manually.

If you go directly to the document and edit the info file without passing through
the ``papis edit`` command, the cache will not be updated and therefore Papis will
not know of these changes, although they will be there. In such cases you will have
to *clear the cache*.

Clearing the cache
^^^^^^^^^^^^^^^^^^

To clear the cache for a given library you can use the ``cache`` command:

.. code::

    papis cache clear

In order to clear and rebuild the cache (i.e., reset it), you can simply run:

.. code::

    papis cache reset

Disabling the cache
^^^^^^^^^^^^^^^^^^^

You can disable the cache using the configuration setting :confval:`use-cache` and set
it to ``False``, e.g.:

.. code:: ini

  [settings]
  use-cache = False

  [books]
  # Use cache for books but don't use for the rest of libraries
  use-cache = True

.. warning::

   The :confval:`use-cache` option is only used by the ``papis`` backend. The other
   backends cannot be disabled if they are chosen using :confval:`database-backend`.

Papis backend
^^^^^^^^^^^^^

Since version ``v0.3``, Papis implements a simple query language to search documents
when using the ``papis`` backend. Queries can contain any field of the info file, so
that ``author:einstein publisher:review`` will match documents that have ``author``
match with ``einstein`` AND ``publisher`` match with ``review`` in a case-insensitive
fashion.

In general, the query syntax is formed of multiple ``[key:]"value"`` matches, where

* the key is optional (searches all keys in this case)
* and the value can be any string (with optional quotes required to include spaces).

.. note::

    Only the ``AND`` filter is implemented in this simple query language.
    Other filters such as ``OR`` or ``NOT`` are not supported. If you need
    this, consider using the `Whoosh backend`_ or the `SQLite backend`_.

.. warning::

    The query syntax does not support Unicode strings. If it encounters a
    Unicode codepoint, it will convert it to the closest looking ASCII letter
    and search for that instead. This can have some surprising results.

For illustration, here are some examples:

- Open documents where the author key matches 'albert' (ignoring case) and
  year matches '05' (i.e. could be '1905' or '2005'):

.. code::

    papis open 'author : albert year : 05'

- Add the restriction to the previous search that the usual matching matches
  the substring 'licht' in addition to the previously selected:

.. code::

    papis open 'author : albert year : 05 licht'

This is not to be mixed with the restriction that the key ``year`` matches
``'05 licht'``, which will not match any year, i.e.:

.. code::

    papis open 'author : albert year : "05 licht"'

Whoosh backend
--------------

Papis can alternatively use the `Whoosh library
<https://whoosh.readthedocs.io/en/latest>`__. This backend can have better
performance when using large libraries.

Of course, the performance comes at a cost. To achieve more performance, Whoosh
needs to create an index with information about the documents. Parsing a user
query means going to the index and matching the query to what is found in the index.
This means that the index can not in general have all the information that the info
file of the documents includes.

In other words, the Whoosh index will store only certain fields from the
documents' info files. The good news is that we can tell Papis exactly which
fields we want to index. These flags are

- :confval:`whoosh-schema-fields`
- :confval:`whoosh-schema-prototype`

The prototype is for advanced users. If you just want to, say, include
the publisher to the fields that you can search in, then you can put:

.. code:: ini

    whoosh-schema-fields = ['publisher']

and you will be able to find documents by their publisher. For example, without
this line set for publisher, the query:

.. code:: bash

  papis open publisher:*

will not return anything, since the publisher field is not being stored.

Query language
^^^^^^^^^^^^^^

The Whoosh database uses the Whoosh query language which is much more
advanced than the query language in the `Papis backend`_.

The Whoosh query language supports both ``AND`` and ``OR`` and other wildcards.
For instance:

- Find papers by Einstein from 1905, or any paper with "einstein" in the title:

.. code:: bash

    papis open '(author:einstein AND year:1905) OR title:einstein'

- Find all papers tagged "physics" or "quantum":

.. code:: bash

    papis open 'tags:physics OR tags:quantum'

- Use a wildcard to find papers whose title starts with "rela":

.. code:: bash

    papis open 'title:rela*'

You can read more about the Whoosh query language
`here <https://whoosh.readthedocs.io/en/latest/querylang.html>`__.

SQLite backend
--------------

This backend is similar to the `Whoosh backend`_ in the way that it functions.
It is expected to be even more performant than the Whoosh backend and it comes
with no additional dependencies. It should be a good first choice if you
notice your library searches are getting sluggish.

To customize the searchable fields by the ``sqlite`` backend, you will also need
to define :confval:`sqlite-schema-fields`. A good default is in place, so this
should not be necessary unless you require complex queries.

Query language
^^^^^^^^^^^^^^

To perform search queries, the ``sqlite`` backend uses the `Full Text Search (FTS5)
<https://sqlite.org/fts5.html>`__ functionality. This allows using ``AND`` and ``OR``
and various groupings of queries, as expected.

For illustration, here are some examples:

- Find papers where the title contains "einstein" (searches all indexed fields):

.. code:: bash

    papis open 'einstein'

- Find papers where the author field contains "einstein" and the year field
  contains "1905":

.. code:: bash

    papis open 'author : einstein AND year : 1905'

- Find papers matching "einstein" or "bohr" anywhere in the indexed fields:

.. code:: bash

    papis open 'einstein OR bohr'

For advanced users, FTS5 also supports **NEAR queries**, which match documents
where two or more terms appear within a specified number of tokens of each other.
The syntax is ``NEAR(phrase1 phrase2, N)`` where *N* is the maximum number of
tokens allowed between the end of the first phrase and the start of the last
(default: 10 if omitted).

- Find papers where "quantum" and "gravity" appear within 5 tokens of each other
  in the title field:

.. code:: bash

    papis open 'title : NEAR(quantum gravity, 5)'

- Find papers where "general" and "relativity" appear close together anywhere in
  the indexed fields:

.. code:: bash

    papis open 'NEAR(general relativity)'

The FTS5 module in :mod:`sqlite3` has a lot more functionality for complex
queries that you can read about `here <https://sqlite.org/fts5.html>`__.
