import papis
import papis.api
from papis.api import status
import papis.utils
import papis.config
import papis.document


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


class Command(papis.commands.Command):
    def init(self):

        self.parser = self.get_subparsers().add_parser(
            "rm",
            help="Delete entry"
        )

        self.add_search_argument()

        self.parser.add_argument(
            "--file",
            help="Remove files from a document instead of the whole folder",
            default=False,
            action="store_true"
        )

        self.parser.add_argument(
            "-f", "--force",
            help="Do not confirm removal",
            default=False,
            action="store_true"
        )

    def main(self):
        documents = self.get_db().query(self.args.search)
        document = self.pick(documents)
        if not document:
            return status.file_not_found
        if self.get_args().file:
            filepath = papis.api.pick(
                document.get_files()
            )
            if not filepath:
                return status.file_not_found
            if not self.args.force:
                if not papis.utils.confirm("Are you sure?"):
                    return status.success
            print("Removing %s..." % filepath)
            return run(
                document,
                filepath=filepath
            )
        else:
            if not self.args.force:
                if not papis.utils.confirm("Are you sure?"):
                    return status.success
            print("Removing ...")
            return run(document)
