#! /usr/bin/env python3
# papis-short-help: Git add <document>.
# Copyright © 2017 Alejandro Gallo. GPLv3

"""
.. note::

    This is just an example script and this functionality is better
    implemented by ``papis git``.

Adds the files in the path of the selected documents to the ``git`` index.
A simple usage of this command is::

    papis ga -a Einstein
"""

import os

import papis.api
import papis.document
import papis.logging

papis.logging.setup()
logger = papis.logging.get_logger("papis.commands.ga")


def add(doc: papis.document.Document) -> None:
    path = os.path.expanduser(papis.config.get_lib_dirs()[0])
    cmd = ["git", "-C", path, "add"] + doc.get_files() + [doc.get_info_file()]

    logger.info("Running command: '%s'", " ".join(cmd))

    import subprocess
    subprocess.call(cmd)


def run(query: str, all_: bool = False) -> int:
    documents = papis.api.get_documents_in_lib(
        papis.api.get_lib_name(),
        search=query
    )

    if all_:
        picked_documents = documents
    else:
        picked_documents = list(papis.api.pick_doc(documents))

    for doc in picked_documents:
        add(doc)

    return 0


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "query",
        default=papis.config.getstring("default-query-string"),
        help="A query to run over the documents")
    parser.add_argument(
        "-a", "--all", dest="all_", action="store_true",
        help="Apply command to all documents returned by the query")
    args = parser.parse_args()

    raise SystemExit(run(args.query, all_=args.all_))
