"""

Cli
^^^
.. click:: papis.commands.rename:cli
    :prog: papis rename
"""
import papis
import os
import papis.pick
import papis.tui.utils
import subprocess
import logging
import click
import papis.cli
import papis.database
import papis.strings
import papis.git
import papis.hg

from typing import Optional


def run(
        document: papis.document.Document,
        new_name: str, git: bool = False, hg: bool = False) -> None:
    db = papis.database.get()
    logger = logging.getLogger('rename:run')
    folder = document.get_main_folder()

    if not folder:
        raise Exception(papis.strings.no_folder_attached_to_document)

    subfolder = os.path.dirname(folder)

    new_folder_path = os.path.join(subfolder, new_name)

    if os.path.exists(new_folder_path):
        logger.warning("Path %s already exists" % new_folder_path)
        return

    cmd = ['git', '-C', folder] if git else ['hg', '--cwd', folder] if hg else []
    cmd += ['mv', folder, new_folder_path]

    logger.debug(cmd)
    subprocess.call(cmd)

    if git and hg:
        hgcmd = ['hg', '--cwd', folder, 'mv', '-A', folder, new_folder_path]
        logger.debug(hgcmd)
        subprocess.call(hgcmd)

    if git:
        papis.git.commit(
            new_folder_path,
            "Rename from {} to '{}'".format(folder, new_name))
    if hg:
        papis.hg.commit(
            new_folder_path,
            [folder, new_folder_path],
            "Rename from {} to '{}'".format(folder, new_name))

    db.delete(document)
    logger.debug("New document folder: {}".format(new_folder_path))
    document.set_folder(new_folder_path)
    db.add(document)


@click.command("rename")
@click.help_option('--help', '-h')
@papis.cli.query_option()
@papis.cli.git_option()
@papis.cli.hg_option()
@papis.cli.sort_option()
def cli(
        query: str,
        git: bool,
        hg: bool,
        sort_field: Optional[str],
        sort_reverse: bool) -> None:
    """Rename entry"""

    documents = papis.database.get().query(query)

    if sort_field:
        documents = papis.document.sort(documents, sort_field, sort_reverse)

    logger = logging.getLogger('cli:rename')

    if not documents:
        logger.warning(papis.strings.no_documents_retrieved_message)
    docs = papis.pick.pick_doc(documents)
    if not docs:
        return

    document = docs[0]

    new_name = papis.tui.utils.prompt(
        "Enter new folder name:\n"
        ">",
        default=document.get_main_folder_name() or ''
    )
    run(document, new_name, git=git, hg=hg)
