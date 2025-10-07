"""
This command allows the user to interact with the Papis cache (database).

To clear the cache (remove it from the filesystem), you can run the following
command:

::

    papis cache clear

This command is also useful for plugin developers.
Let us suppose that you are editing the YAML file of a document at path
``/path/to/info.yaml``.
If you are editing this file without the machinery of Papis
you might want to make Papis aware of this change by using the ``update``
subcommand. You might do:

::

    papis cache update --doc-folder /path/to

or maybe by query:

::

    papis cache update query-matching-document

Furthermore, a noteworthy subcommand is ``update-newer``, which
updates the cache for those documents whose info file is newer than
the cache itself.  This subcommand has the same interface as most
``papis`` commands, so that if you want to check all documents you have to
input:

::

        papis cache update-newer --all

This command is much faster than rebuilding the cache from scratch.
You can therefore run this command once in a while in order to update
the cache for those documents that have been synchronized by the means
of synchronization that you are using, for instance using git, Syncthing,
Dropbox, etc.

Command-line interface
^^^^^^^^^^^^^^^^^^^^^^

.. click:: papis.commands.cache:cli
    :prog: papis cache
    :nested: full
"""
import os

import click

import papis.cli
from papis.commands import AliasedGroup

logger = papis.logging.get_logger(__name__)


@click.group("cache",
             cls=AliasedGroup,
             invoke_without_command=False,
             chain=False)
@click.help_option("--help", "-h")
def cli() -> None:
    """
    Manage the cache (database) of a Papis library.
    """


@cli.command("update")
@click.help_option("--help", "-h")
@papis.cli.query_argument()
@papis.cli.doc_folder_option()
@papis.cli.all_option()
@papis.cli.sort_option()
def update(query: str,
           doc_folder: tuple[str, ...],
           _all: bool,
           sort_field: str | None,
           sort_reverse: bool) -> None:
    """
    Reload info.yaml files from disk and update the cache.
    """
    from papis.database import get_database

    db = get_database()
    documents = papis.cli.handle_doc_folder_query_all_sort(
        query, doc_folder, sort_field, sort_reverse, _all)

    if not documents:
        from papis.strings import no_documents_retrieved_message
        logger.warning(no_documents_retrieved_message)
        return

    for doc in documents:
        doc.load()
        db.update(doc)

    logger.info("Updated %d documents", len(documents))


@cli.command("clear")
@click.help_option("--help", "-h")
def clear() -> None:
    """
    Clear the cache from disk.

    The next invocation of any command that uses the cache will rebuild it.
    """
    from papis.database import get_database

    db = get_database()
    db.clear()


@cli.command("reset")
@click.help_option("--help", "-h")
def reset() -> None:
    """
    Reset the cache (clear and rebuild).
    """
    from papis.database import get_database

    db = get_database()
    db.clear()
    db.initialize()
    _ = db.get_all_documents()


@cli.command("add")
@click.help_option("--help", "-h")
@papis.cli.doc_folder_option()
def add(doc_folder: tuple[str, ...]) -> None:
    """
    Add a document to the cache.

    This is useful for adding single folders from a previous synchronization step.
    """
    from papis.database import get_database
    db = get_database()

    from papis.document import describe, from_folder

    for d in doc_folder:
        doc = from_folder(d)
        if not doc:
            logger.error("The path '%s' did not contain a valid 'info.yaml' file.",
                         doc_folder)
            continue

        db.add(doc)
        logger.info("Successfully added '%s' to the cache.", describe(doc))


@cli.command("rm")
@click.help_option("--help", "-h")
@papis.cli.query_argument()
@papis.cli.doc_folder_option()
@papis.cli.all_option()
@papis.cli.sort_option()
def rm(query: str,
       doc_folder: tuple[str, ...],
       _all: bool,
       sort_field: str | None,
       sort_reverse: bool) -> None:
    """
    Delete documents from the cache.
    """
    from papis.database import get_database

    documents = papis.cli.handle_doc_folder_query_all_sort(
        query, doc_folder, sort_field, sort_reverse, _all)

    db = get_database()
    for doc in documents:
        db.delete(doc)

    logger.info("Removed %d documents from cache", len(documents))


@cli.command("pwd")
@click.help_option("--help", "-h")
def pwd() -> None:
    """
    Print the path to the cache file or directory.
    """
    from papis.database import get_database

    db = get_database()
    click.echo(db.get_cache_path())


@cli.command("update-newer")
@click.help_option("--help", "-h")
@papis.cli.query_argument()
@papis.cli.doc_folder_option()
@papis.cli.all_option()
@papis.cli.sort_option()
def update_newer(query: str,
                 doc_folder: tuple[str, ...],
                 _all: bool,
                 sort_field: str | None,
                 sort_reverse: bool) -> None:
    """
    Update documents newer than the cache modification time.
    """
    from papis.database import get_database
    db = get_database()

    documents = papis.cli.handle_doc_folder_query_all_sort(
        query, doc_folder, sort_field, sort_reverse, _all)

    if not documents:
        from papis.strings import no_documents_retrieved_message
        logger.warning(no_documents_retrieved_message)
        return

    updated_documents_count = 0
    cache_path = db.get_cache_path()
    cache_path_mtime = os.stat(cache_path).st_mtime

    from papis.document import describe

    for doc in documents:
        info = doc.get_info_file()
        if not os.path.exists(info):
            continue

        info_mtime = os.stat(info).st_mtime
        if cache_path_mtime < info_mtime:
            updated_documents_count += 1
            logger.info("Updating newer '%s'.", describe(doc))

            doc.load()
            db.update(doc)

    logger.info("Updated %d documents.", updated_documents_count)
