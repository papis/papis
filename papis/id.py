"""
The ``papis_id`` key
--------------------

Every papis document should have a ``papis_id`` key created at random by
the papis database.

If you manually add a document into your library, you will have to clear
the library cache

.. code:: sh

    papis --cc

in order to trigger a database building the next time that you issue
a papis command. When the library scans the document added manually,
it will create a ``papis_id`` key automatically and **it will edit** your
``info.yaml`` file accordingly.
We stress again that the database will **edit** the ``info.yaml`` file,
without committing the changes (in the case that you are using a git
repository), so that you can inspect the changes manually.

Please note that if you add a document manually with an existing
``papis_id`` to your library, papis will not check if there is an
id clash. A clash of ids has a very low probability.
Please refer to the ``papis-doctor`` help for checking for clashes.

Use of ``papis_id`` in scripts
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Since the ``papis_id`` key is a unique identifier, it is quite
useful for scripts that do not depend on the actual path
to the document in your system.

For instance you can get the ``papis_id`` of a document
in ``bash`` like such

.. code:: sh

    id=$(papis list --id)

and subsequently use the ``id`` variable to trigger other commands,
for instance you can open the file attached to the document like
such

.. code:: sh

    papis open papis_id:${id}

"""
from typing import Optional, Dict, Any
import hashlib
import random

import papis.document


def compute_an_id(doc: papis.document.Document,
                  separator: Optional[str] = None) -> str:
    """
    Get a random id seeded in part by the input document.
    Note: this is a non-deterministic function if separator is None.
    For a determined value of separator, the result is deterministic.
    """
    separator = separator if separator is not None else str(random.random())
    string = separator.join([
        str(doc),
        str(doc.get_files()),
        str(doc.get_info_file()),
    ])
    return hashlib.md5(string.encode()).hexdigest()


def key_name() -> str:
    """
    Reserved key name for databases and documents.
    """
    return "papis_id"


def has_id(doc: Dict[str, Any]) -> bool:
    """
    Checks if a dictionary is potentially an identified papis
    document.
    """
    return key_name() in doc


def get(doc: Dict[str, Any]) -> str:
    """
    Get the id from a document.
    """
    key = key_name()
    if not has_id(doc):
        raise ValueError(
            "Papis ID key '{}' not found in document: '{}'"
            .format(key, papis.document.describe(doc)))

    return str(doc[key])
