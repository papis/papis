Query language
==============

Since version `0.3` there is a query language in place for the searching
of documents. To illustrate it here are some examples:

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

