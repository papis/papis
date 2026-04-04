The ``papis_id`` key
--------------------

Every Papis document should have a ``papis_id`` key created at random by
the Papis database. This id should serve as a UUID-type key for the document
(by default it contains a hash of the document keys and documents with a bit
of randomness thrown in).

The ``papis_id`` is added automatically when using ``papis add`` or other commands,
but is not updated after the initial creation of the document. If you manually
add a document into your library, e.g. by creating an ``info.yaml`` file without
Papis, you will have to clear the library cache in order to trigger a rebuild
using:

.. code:: sh

    papis cache clear

When the library scans the document added manually, it will create a ``papis_id``
key automatically and **it will edit** your ``info.yaml`` file accordingly.
We stress again that the database will **edit** the ``info.yaml`` file,
without committing the changes (in the case that you are using a git
repository), so that you can inspect the changes manually.

Please note that if you add a document manually with an existing
``papis_id`` to your library, Papis will not check if there is an
id clash. A clash of ids has a very low probability and can be checked using
the ``papis doctor`` command.

Use of ``papis_id`` in scripts
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Since the ``papis_id`` key is a unique (ish) identifier, it is quite useful for
scripts that do not depend on the actual path to the document in your system.

For instance you can get the ``papis_id`` of a document using:

.. code:: sh

    id=$(papis list --id query)

and subsequently use the ``id`` variable to trigger other commands. For example,
you can open the files attached to the document using:

.. code:: sh

    papis open "papis_id:${id}"

