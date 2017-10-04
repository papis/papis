FAQ
===

Here are some problems that users have come accross with often:

- When I remove a folder manually in a library or I synchronize manually
  the library I do not see the new papers in the library.
  **Answer**: You probably need to update the cache because papis did not
  know anything about your changes in the library since you did it by yourself.

  .. code::

    papis --clear-cache

  will do.
