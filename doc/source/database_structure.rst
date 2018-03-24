The database
============

One of the things that makes papis interesting is the fact that
there can be many backends for the database system, including no database.

Right now there are three types of database in that the user can use:

- No database
- Simple cache based database
- `Whoosh <https://whoosh.readthedocs.io/en/latest>`_  based database.

If you just plan to have or have few dozen of documents in your library,
probably you'll have ample performance with the two first options.
However if you're reaching higher numbers, 500, 1000, 2000 documents,
you'll probably want to use the ``Whoosh`` backend for very good performance.

You can select the databases using the flag
:ref:`database-backend <config-settings-database-backend>`.

Papis database
--------------

The fact that there is no database means that papis should crawl through
the library folder and see which folders have an ``info.yaml`` file, which
is for slow computers quite bad.

Papis implements a very rudimentary caching system. A cache is created for
every library. Inside the cache only the paths to the different valid papis
documents are stored.

These cache files are stored per default in

::

  ~/.cache/papis/

Some papis commands update the cache automatically, for example the ``add`` and
``rm`` command clear the cache when something is changed.

Clearing the cache
^^^^^^^^^^^^^^^^^^

To clear the cache for a given library you can use the flag
``--clear-cache``, e.g.

.. code::

    papis --clear-cache

Query language
^^^^^^^^^^^^^^

Since version `0.3` there is a query language in place for the searching
of documents.
The queries can contain any field of the info file, i.e.,
``author=einstein publisher = review`` will match documents that have
a matching ``author`` with ``einstein`` AND having a ``publisher``
matching ``review``.
The AND part here is important, since
only the ``AND`` filter is implemented in this simple query
language, at the moment it is not possible to do an ``OR``.
If you need this, you should consider using the
`Whoosh database`_.


To illustrate it here are some examples:

  - Open documents where the author key matches 'albert' (ignoring case),
    year matches '19' (i.e., 1990, 2019, 1920):

    .. code::

      papis open 'author = albert year = 05'

  - Add the restriction to the previous search that the usual matching matches
    the substring 'licht' in addition to the previously selected

    .. code::

      papis open 'author = albert year = 05 licht'

    This is not to be mixed with the restriction that the key `year` matches
    `'05 licht'`, which will not match any year, i.e.

    .. code::

      papis open 'author = albert year = "05 licht"'


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
`Whoosh library <https://whoosh.readthedocs.io/en/latest>`_.
Its performance is orders of magnitude better than the crude cache based
database.

Query language
^^^^^^^^^^^^^^

The whoosh database uses the whoosh query language which is much more
advanced than the query language in the `Papis database`_.

You can read more about the whoosh query language
`here <https://whoosh.readthedocs.io/en/latest/querylang.html>`_.
