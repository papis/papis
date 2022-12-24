Citations
---------

The ``citations`` command updates and creates the ``citations.yaml`` and
``cited.yaml`` files for every document.

Examples
~~~~~~~~

- Create the ``citations.yaml`` file for a document that you pick

  .. code:: sh

      papis citations -c

  or longer

  .. code:: sh

      papis citations --fetch-citations

- Create the ``citations.yaml`` file for all documents matching an author

  .. code:: sh

      papis citations --all -c author:einstein

- Overwrite the ``citations.yaml`` file with the ``--force`` flag for all Einstein papers

  .. code:: sh

      papis citations --force -c author:einstein
      # or
      papis citations -fc author:einstein

- Update the ``citations.yaml`` file with citations of documents existing in your library

  .. code:: sh

      papis citations --all --update-from-database author:einstein

- Create the ``cited-by.yaml`` for all documents in your library (this might take a while)

  .. code:: sh

      papis citations --fetch-cited-by --all
