import hashlib
import random
from warnings import warn

import papis.logging
from papis.document import Document, DocumentLike

logger = papis.logging.get_logger(__name__)

#: Key name used to store the Papis ID. This key name is reserved for use in
#: Papis databases and documents. It can also change in the future, so it is
#: recommended to use this variable instead of hardcoding the name.
ID_KEY_NAME: str = "papis_id"


def compute_an_id(doc: Document, separator: str | None = None) -> str:
    """Make an ID for the input document *doc*.

    This is a non-deterministic function if *separator* is *None* (a random value
    is used). For a given value of *separator*, the result is deterministic.

    :arg doc: a document for which to generate an ID.
    :arg separator: a string used to separate the document fields that go into
        constructing the ID.

    :returns: a (hexadecimal) ID for the document that is unique to high probability.
    """
    if separator is None:
        separator = str(random.random())

    string = separator.join([
        str(doc),
        str(doc.get_files()),
        str(doc.get_info_file()),
    ])

    return hashlib.md5(string.encode()).hexdigest()


def key_name() -> str:
    """Get Papis ID key name."""
    warn("This function is deprecated and will be removed in the next "
         "version of Papis (after 0.15). Use 'papis.id.ID_KEY_NAME' instead.",
         DeprecationWarning, stacklevel=2)

    return ID_KEY_NAME


def has_id(doc: DocumentLike) -> bool:
    warn("This function is deprecated and will be removed in the next "
         "version of Papis (after 0.15). Check for the 'papis.id.ID_KEY_NAME' "
         "key directly in the document instead.",
         DeprecationWarning, stacklevel=2)

    return ID_KEY_NAME in doc


def get(doc: DocumentLike) -> str:
    """Get the Papis ID from *doc*.

    This function does additional checking on the ID and can raise an error if it
    does not exist. If the ID is known to exist, use :data:`ID_KEY_NAME` directly.
    """

    doc_id = doc.get(ID_KEY_NAME)
    if doc_id is None:
        from papis.document import describe

        raise ValueError(
            f"Papis ID key '{ID_KEY_NAME}' not found in document: '{describe(doc)}'"
            )

    if isinstance(doc_id, str):
        return doc_id
    else:
        from papis.document import describe

        logger.warning("The Papis ID '%s' is not a string '%s': %s.",
                       ID_KEY_NAME, type(doc_id), describe(doc))
        return str(doc_id)
