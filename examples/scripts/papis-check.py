#! /usr/bin/env python3
# papis-short-help: Check document keys
# Copyright © 2018 Alejandro Gallo. GPLv3

"""
.. note::

    This is just an example script and more comprehensive checks are implemented
    by ``papis doctor``.

This command checks for several attributes in every document.

For example, if you want to check that every document in your library has valid
files attached to it, you can just do::

    papis check --key files

This will check that every ``info.yml`` file has the key ``"files"`` and that
every file listed exists on the filesystem.

You can also define more complicated checks, e.g., if you want to check that
every document has files, a valid author and title::

    papis check --key files --key author --key title

Command Options
^^^^^^^^^^^^^^^

.. papis-config:: keys
    :section: check

    A list of key values to be checked by default by the command
    ``check``. E.g: ``check-keys = ["author", "doi"]``.
"""

import os
from typing import Any, Dict, List, Sequence

import click

import papis.api
import papis.cli
import papis.config
import papis.document
import papis.logging

papis.logging.setup()
logger = papis.logging.get_logger("papis.commands.check")

papis.config.register_default_settings({
    "check": {
        "keys": ["files"],
    }
})


def check_files(document: papis.document.Document) -> bool:
    """Check for the existence of the document's files.

    :returns: *False* if some file does not exist, *True* otherwise

    >>> from papis.document import from_data
    >>> doc = from_data({'title': 'Hello World'})
    >>> doc['files'] = ['nonexistent.pdf']
    >>> import tempfile; doc.set_folder(tempfile.mkdtemp())
    >>> check_files(doc)
    ** Error: .../nonexistent.pdf not found in ...
    False
    """
    for f in document.get_files():
        # document.logger.debug(f)
        if not os.path.exists(f):
            logger.error("'%s' not found in '%s'.", f, document.get_main_folder())
            return False
        else:
            return True

    return True


def run(keys: Sequence[str],
        documents: Sequence[papis.document.Document],
        ) -> Sequence[Dict[str, Any]]:
    result = []
    for document in documents:
        for key in keys:
            if key not in document:
                result.append({"doc": document, "key": key, "msg": "Missing key"})
            elif not document[key] and document[key] is not False:
                result.append({"doc": document, "key": key, "msg": "Empty key"})
            elif key == "files":
                if not check_files(document):
                    result.append({"doc": document, "key": key, "msg": "Missing files"})

    return result


@click.command()
@click.help_option("--help", "-h")
@papis.cli.query_argument()
@click.option(
    "--key", "-k", "keys",
    help="Space separated fields to check against",
    multiple=True,
    default=lambda: papis.config.getlist("keys", section="check")
)
def cli(query: str, keys: List[str]) -> None:
    """Check document from a given library"""
    documents = papis.database.get().query(query)
    troubled_docs = run(keys, documents)

    for doc in troubled_docs:
        print(
            "{key} - {folder}: {msg}".format(
                key=doc["key"],
                folder=doc["doc"].get_main_folder(),
                msg=doc["msg"],
            )
        )

    if not len(troubled_docs) == 0:
        logger.error("Errors were detected, please fix the info files")
    else:
        logger.info("No errors detected")


if __name__ == "__main__":
    cli()
