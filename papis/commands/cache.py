"""
This command allows the user to interact with the papis cache or papis database.

To clear the cache (remove it from the filesystem), you can run the following
command

::

    papis cache clear

This command is also useful for plugin developers.
Let us suppose that you are editing the YAML file of a document at path
``/path/to/info.yaml``.
If you are editing this file without the machinery of papis
you might want to make papis be aware of this change by using the ``update``
subcommand. You might do

::

    papis cache update --doc-folder /path/to

or maybe by query

::

    papis cache update query-matching-document

Furthermore, a noteworthy subcommand is ``update-newer``, which
updates the cache for those documents whose info file is newer than
the cache itself.  This subcommand has the same interface as most
papis commands, so that if you want to check all documents you have to
input

::

        papis cache update-newer --all

This command is much faster than rebuilding the cache from scratch.
You can therefore run this command once in a while in order to update
the cache for those documents that have been synchronised by the means
of synchronization that you are using, for instance using git, Syncthing,
Dropbox, etc.

"""
import os
from typing import Optional

import click

import papis.commands
import papis.document
import papis.strings
import papis.cli

logger = papis.logging.get_logger(__name__)


@click.group("cache",
             cls=papis.commands.AliasedGroup,
             invoke_without_command=False,
             chain=False)
@click.help_option("--help", "-h")
def cli() -> None:
    """
    Manage the cache or database of a papis library.
    """


@cli.command("update")
@click.help_option("--help", "-h")
@papis.cli.query_argument()
@papis.cli.doc_folder_option()
@papis.cli.all_option()
@papis.cli.sort_option()
def update(query: str, doc_folder: str, _all: bool, sort_field: Optional[str],
           sort_reverse: bool) -> None:
    """
    Reload the yaml file from disk and update the cache with that information.
    """
    db = papis.database.get()
    documents = papis.cli.handle_doc_folder_query_all_sort(
        query, doc_folder, sort_field, sort_reverse, _all)

    if not documents:
        logger.warning(papis.strings.no_documents_retrieved_message)
        return

    for doc in documents:
        doc.load()
        db.update(doc)

    logger.info("Updated %d documents", len(documents))


@cli.command("clear")
@click.help_option("--help", "-h")
def clear() -> None:
    """
    Clear the cache of the library completely.

    The next invocation of papis will rebuild the cache.
    """
    papis.database.get().clear()


@cli.command("reset")
@click.help_option("--help", "-h")
def reset() -> None:
    """
    Resets the cache, i.e., it clears the cache and then
    builds it.
    """
    papis.database.get().clear()
    papis.database.get().get_all_documents()


@cli.command("add")
@click.help_option("--help", "-h")
@papis.cli.doc_folder_option()
def add(doc_folder: str) -> None:
    """
    Adds a folder path to the papis cache, i.e., to the database.

    This might be useful for adding single folders from a previous
    synchronization step.
    """
    doc = papis.document.from_folder(doc_folder)

    if not doc:
        logger.error(
            "The path '%s' did not contain any useful papis information.",
            doc_folder)
        return

    db = papis.database.get()
    db.add(doc)

    logger.info("Succesfully added %s to the cache",
                papis.document.describe(doc))


@cli.command("rm")
@click.help_option("--help", "-h")
@papis.cli.query_argument()
@papis.cli.doc_folder_option()
@papis.cli.all_option()
@papis.cli.sort_option()
def rm(query: str, doc_folder: str, _all: bool, sort_field: Optional[str],
       sort_reverse: bool) -> None:
    """
    Delete document from the cache, the disk data however will not be touched.
    """

    documents = papis.cli.handle_doc_folder_query_all_sort(
        query, doc_folder, sort_field, sort_reverse, _all)

    db = papis.database.get()
    for doc in documents:
        db.delete(doc)

    logger.info("Removed %d documents from cache", len(documents))


@cli.command("pwd")
@click.help_option("--help", "-h")
def pwd() -> None:
    """
    Print the path to the cache file or directory.
    """
    print(papis.database.get().get_cache_path())


@cli.command("update-newer")
@click.help_option("--help", "-h")
@papis.cli.query_argument()
@papis.cli.doc_folder_option()
@papis.cli.all_option()
@papis.cli.sort_option()
def update_newer(query: str, doc_folder: str, _all: bool,
                 sort_field: Optional[str], sort_reverse: bool) -> None:
    """
    Reload the yaml file from disk only of those documents whose info
    file is newer than the cache.
    """
    db = papis.database.get()
    documents = papis.cli.handle_doc_folder_query_all_sort(
        query, doc_folder, sort_field, sort_reverse, _all)

    if not documents:
        logger.warning(papis.strings.no_documents_retrieved_message)
        return

    updated_documents_n = 0
    cache_path = db.get_cache_path()

    for doc in documents:
        info = doc.get_info_file()

        if not os.path.exists(info):
            continue

        if os.stat(cache_path).st_mtime < os.stat(info).st_mtime:
            updated_documents_n += 1
            logger.info("Updating %s", papis.document.describe(doc))
            doc.load()
            db.update(doc)

    logger.info("Updated %d documents", updated_documents_n)
