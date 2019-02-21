"""

Cli
^^^
.. click:: papis.commands.rename:cli
    :prog: papis rename
"""
import papis
import os
import papis.api
import papis.utils
import subprocess
import logging
import click
import papis.cli
import papis.database


def run(document, new_name, git=False):
    db = papis.database.get()
    logger = logging.getLogger('rename:run')
    folder = document.get_main_folder()
    subfolder = os.path.dirname(folder)

    new_folder_path = os.path.join(subfolder, new_name)

    if os.path.exists(new_folder_path):
        logger.warning("Path %s already exists" % new_folder_path)
        return 1

    cmd = ['git', '-C', folder] if git else []
    cmd += ['mv', folder, new_folder_path]

    logger.debug(cmd)
    subprocess.call(cmd)

    if git:
        papis.utils.git_commit(message="Rename %s" % folder)

    db.delete(document)
    logger.debug("New document folder: {}".format(new_folder_path))
    document.set_folder(new_folder_path)
    db.add(document)
    return 0


@click.command()
@click.help_option('--help', '-h')
@papis.cli.query_option()
@papis.cli.git_option()
def cli(query, git):
    """Rename entry"""

    documents = papis.database.get().query(query)
    document = papis.api.pick_doc(documents)
    if not document:
        return 0

    new_name = papis.utils.input(
        "Enter new folder name:\n"
        ">",
        default=document.get_main_folder_name()
    )
    return run(document, new_name, git=git)
