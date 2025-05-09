FAQ
===

Here are some problems that users have come across often:

- **Question**: When I remove a folder manually in a library or I synchronize
  the library manually, I do not see the new papers in the library.

  **Answer**: You probably need to update the cache because Papis did not know
  anything about your changes in the library since you did it by yourself. Run:

  .. code::

    papis cache update-newer

  or (as a last resort)

  .. code::

    papis cache reset

For responses to other frequently asked questions, check out our
`GitHub issues labeled with faq <https://github.com/papis/papis/issues?utf8=%E2%9C%93&q=label:faq>`__.
