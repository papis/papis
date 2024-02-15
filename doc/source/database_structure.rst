The database
============

One of the things that makes papis interesting is the fact that
there can be many backends for the database system, including no database.

Right now there are three types of databases that the user can use:

- No database
    ::

      database-backend = papis
      use-cache = False

- Simple cache based database.
    ::

      database-backend = papis

- `Whoosh <https://whoosh.readthedocs.io/en/latest>`__  based database.
    ::

      database-backend = whoosh

If you just plan to have up to 3000 documents in your library,
you will have ample performance with the two first options.
However if you're reaching higher numbers,
you'll probably want to use the ``Whoosh`` backend for very good performance.

You can select a database by using the flag :confval:`database-backend`.

Papis database
--------------

The fact that there is no database means that papis should crawl through
the library folder and see which folders have an ``info.yaml`` file, which
is for slow computers (and harddrives) quite bad.

Papis implements a very rudimentary caching system. A cache is created for
every library. Inside the cache the whole information already converted
into python is stored.

These cache files are stored per default in

::

  ~/.cache/papis/

Notice that most papis commands will update the cache if it has to be the case.
For instance the ``edit`` command will let you edit your document's information
and after you are done editing it will update the information for the given
document in the cache.
If you go directly to the document and edit the info file without
passing through the papis edit command, the cache will not be updated and
therefore papis will not know of these changes, although they will be there.
In such cases you will have to *clear the cache*.

Clearing the cache
^^^^^^^^^^^^^^^^^^

To clear the cache for a given library you can use the command ``cache``
thusly

.. code::

    papis cache clear

In order to clear and rebuild the cache (i.e., reset it), you can simply run

.. code::

    papis cache reset

Query language
^^^^^^^^^^^^^^

Since version `0.3` there is a query language in place for the searching
of documents.
The queries can contain any field of the info file, e.g.,
``author:einstein publisher : review`` will match documents that have
a matching ``author`` with ``einstein`` AND have a ``publisher``
matching ``review``.
The AND part here is important, since
only the ``AND`` filter is implemented in this simple query
language. At the moment it is not possible to do an ``OR``.
If you need this, you should consider using the
`Whoosh database`_.

For illustration, here are some examples:

  - Open documents where the author key matches 'albert' (ignoring case) and
    year matches '19' (i.e., 1990, 2019, 1920):

    .. code::

      papis open 'author : albert year : 05'

  - Add the restriction to the previous search that the usual matching matches
    the substring 'licht' in addition to the previously selected

    .. code::

      papis open 'author : albert year : 05 licht'

    This is not to be mixed with the restriction that the key `year` matches
    `'05 licht'`, which will not match any year, i.e.

    .. code::

      papis open 'author : albert year : "05 licht"'


Disabling the cache
^^^^^^^^^^^^^^^^^^^

You can disable the cache using the configuration setting ``use-cache``
and set it to ``False``, e.g.

.. code:: ini

  [settings]

  use-cache = False

  [books]
  # Use cache for books but don't use for the rest of libraries
  use-cache = True


Whoosh database
---------------

Papis has also the possibility to use the blazing fast and pure python
`Whoosh library <https://whoosh.readthedocs.io/en/latest>`__.
Its performance is orders of magnitude better than the crude cache based
database.

Of course, the performance comes at a cost. To achieve more performance
a database backend should create an index with information about the documents.
Parsing a user query means going to the index and matching the query to
what is found in the index. This means that the index can not in general
have all the information that the info file of the documents includes.

In other words, the whoosh index will store only certain fields from the
document's info files. The good news is that we can tell papis exactly
which fields we want to index. These flags are

- :confval:`whoosh-schema-fields`
- :confval:`whoosh-schema-prototype`

The prototype is for advanced users. If you just want to, say, include
the publisher to the fields that you can search in, then you can put

::

  whoosh-schema-fields = ['publisher']

and you will be able to find documents by their publisher.
For example, without this line set for publisher, the query

::

  papis open publisher:*

will not return anything, since the publisher field is not being stored.


Query language
^^^^^^^^^^^^^^

The whoosh database uses the whoosh query language which is much more
advanced than the query language in the `Papis database`_.

The whoosh query language supports both ``AND`` and ``OR``, for instance

::

  papis open '(author:einstein AND year:1905) OR title:einstein'

will give papers of einstein in the year 1905 together with all papers
where einstein appears in the title.

You can read more about the whoosh query language
`here <https://whoosh.readthedocs.io/en/latest/querylang.html>`__.
