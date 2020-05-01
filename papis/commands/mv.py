"""

Cli
^^^
.. click:: papis.commands.mv:cli
    :prog: papis mv
"""
import os
import subprocess
import logging
import click

import papis.config
import papis.utils
import papis.database
import papis.document
import papis.cli
import papis.pick
import papis.strings

from typing import Optional


def run(document: papis.document.Document,
        new_folder_path: str,
        git: bool = False) -> None:
    logger = logging.getLogger('mv:run')
    folder = document.get_main_folder()
    if not folder:
        raise Exception(papis.strings.no_folder_attached_to_document)
    cmd = ['git', '-C', folder] if git else []
    cmd += ['mv', folder, new_folder_path]
    db = papis.database.get()
    logger.debug(cmd)
    subprocess.call(cmd)
    db.delete(document)
    new_document_folder = os.path.join(
        new_folder_path,
        os.path.basename(folder))
    logger.debug("New document folder: {}".format(new_document_folder))
    document.set_folder(new_document_folder)
    db.add(document)


@click.command("mv")
@click.help_option('--help', '-h')
@papis.cli.query_option()
@papis.cli.git_option()
@papis.cli.sort_option()
@papis.cli.doc_folder_option()
def cli(query: str,
        git: bool,
        sort_field: Optional[str],
        doc_folder: str,
        sort_reverse: bool) -> None:
    """Move a document into some other path"""
    # Leave this imports here for performance
    import prompt_toolkit
    import prompt_toolkit.completion

    logger = logging.getLogger('cli:mv')

    if doc_folder:
        documents = [papis.document.from_folder(doc_folder)]
    else:
        documents = papis.database.get().query(query)

    if not documents:
        logger.warning(papis.strings.no_documents_retrieved_message)
        return

    if sort_field:
        documents = papis.document.sort(documents, sort_field, sort_reverse)

    docs = papis.pick.pick_doc(documents)
    if not docs:
        return
    document = docs[0]

    lib_dir = os.path.expanduser(papis.config.get_lib_dirs()[0])

    completer = prompt_toolkit.completion.PathCompleter(
        only_directories=True,
        get_paths=lambda: [lib_dir]
    )

    try:
        new_folder = os.path.join(
            lib_dir,
            prompt_toolkit.prompt(
                message=(
                    "Enter directory  : (Tab completion enabled)\n"
                    "Current directory: ({dir})\n".format(
                        dir=document.get_main_folder_name()
                    ) +
                    ">  "
                ),
                completer=completer,
                complete_while_typing=True
            ))
    except Exception as e:
        logger.error(e)
        return

    logger.info(new_folder)

    if not os.path.exists(new_folder):
        logger.info("Creating path %s" % new_folder)
        os.makedirs(new_folder, mode=papis.config.getint('dir-umask') or 0o666)

    run(document, new_folder, git=git)
