"""

Cli
^^^
.. click:: papis.commands.rm:cli
    :prog: papis rm
"""
import papis
import papis.api
from papis.api import status
import papis.utils
import papis.config
import papis.document
import papis.cli
import papis.database
import click


def run(
        document,
        filepath=None
        ):
    """Main method to the rm command

    :returns: List different objects
    :rtype:  list
    """
    db = papis.database.get()
    if filepath is not None:
        document.rm_file(filepath)
        document.save()
    else:
        papis.document.delete(document)
        db.delete(document)
    return status.success


@click.command()
@click.help_option('-h', '--help')
@papis.cli.query_option()
@click.option(
    "--file",
    help="Remove files from a document instead of the whole folder",
    is_flag=True,
    default=False
)
@click.option(
    "-f", "--force",
    help="Do not confirm removal",
    is_flag=True,
    default=False
)
def cli(
        query,
        file,
        force
        ):
    """Delete command for several objects"""
    documents = papis.database.get().query(query)
    document = papis.api.pick_doc(documents)
    if not document:
        return status.file_not_found
    if file:
        filepath = papis.api.pick(
            document.get_files()
        )
        if not filepath:
            return status.file_not_found
        if not force:
            toolbar = 'The file {0} would be removed'.format(filepath)
            if not papis.utils.confirm("Are you sure?", bottom_toolbar=toolbar):
                return status.success
        click.echo("Removing %s..." % filepath)
        return run(
            document,
            filepath=filepath
        )
    else:
        if not force:
            toolbar = 'The folder {0} would be removed'.format(
                document.get_main_folder()
            )
            if not papis.utils.confirm("Are you sure?", bottom_toolbar=toolbar):
                return status.success
        click.echo("Removing ...")
        return run(document)
