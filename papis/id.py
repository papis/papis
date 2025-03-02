import hashlib
import random
from typing import Optional

import papis.document


def compute_an_id(doc: papis.document.Document,
                  separator: Optional[str] = None) -> str:
    """Make an id for the input document *doc*.

    This is a non-deterministic function if *separator* is *None* (a random value
    is used). For a given value of *separator*, the result is deterministic.

    :arg doc: a document for which to generate an id.
    :arg separator: a string used to separate the document fields that go into
        constructing the id.

    :returns: a (hexadecimal) id for the document that is unique to high probability.
    """

    separator = separator if separator is not None else str(random.random())
    string = separator.join([
        str(doc),
        str(doc.get_files()),
        str(doc.get_info_file()),
    ])

    return hashlib.md5(string.encode()).hexdigest()


def key_name() -> str:
    """Reserved key name for databases and documents."""
    return "papis_id"


def has_id(doc: papis.document.DocumentLike) -> bool:
    """Check if the given *doc* has an id."""
    return key_name() in doc


def get(doc: papis.document.DocumentLike) -> str:
    """Get the id from a document."""
    key = key_name()

    if not has_id(doc):
        raise ValueError(
            f"Papis ID key '{key}' not found in document: "
            f"'{papis.document.describe(doc)}'")

    return str(doc[key])
