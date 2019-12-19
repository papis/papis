"""

Cli
^^^
.. click:: papis.commands.mv:cli
    :prog: papis mv
"""
import papis
import os
import papis.config
import papis.utils
import papis.database
import subprocess
import logging
import papis.cli
import papis.pick
import papis.strings
import click


def run(document, new_folder_path, git=False):
    logger = logging.getLogger('mv:run')
    folder = document.get_main_folder()
    cmd = ['git', '-C', folder] if git else []
    cmd += ['mv', folder, new_folder_path]
    db = papis.database.get()
    logger.debug(cmd)
    subprocess.call(cmd)
    db.delete(document)
    new_document_folder = os.path.join(
        new_folder_path,
        os.path.basename(document.get_main_folder())
    )
    logger.debug("New document folder: {}".format(new_document_folder))
    document.set_folder(new_document_folder)
    db.add(document)


@click.command("mv")
@click.help_option('--help', '-h')
@click.option(
    "--sort",
    "sort_field",
    help="Sort results by field",
    default=None
)
@papis.cli.query_option()
@papis.cli.git_option()
def cli(query, git, sort_field):
    """Move a document into some other path"""
    # Leave this imports here for performance
    import prompt_toolkit
    import prompt_toolkit.completion

    logger = logging.getLogger('cli:mv')

    documents = papis.database.get().query(query, sort_field)
    if not documents:
        logger.warning(papis.strings.no_documents_retrieved_message)
        return

    document = papis.pick.pick_doc(documents)
    if not document:
        return 0

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
            )
        )
    except:
        return 0

    logger.info(new_folder)

    if not os.path.exists(new_folder):
        logger.info("Creating path %s" % new_folder)
        os.makedirs(new_folder, mode=papis.config.getint('dir-umask'))

    run(document, new_folder, git=git)
