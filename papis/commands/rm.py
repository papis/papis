import papis
import sys
import os
import shutil
import papis.utils


class Rm(papis.commands.Command):
    def init(self):
        """TODO: Docstring for init.

        :subparser: TODO
        :returns: TODO

        """

        self.parser = self.get_subparsers().add_parser(
            "rm",
            help="Delete entry"
        )
        self.parser.add_argument(
            "document",
            help="Document search",
            nargs="?",
            default=".",
            action="store"
        )
        self.parser.add_argument(
            "-f", "--force",
            help="Do not confirm removal",
            default=False,
            action="store_true"
        )

    def main(self, args):
        """
        Main action if the command is triggered

        :config: User configuration
        :args: CLI user arguments
        :returns: TODO

        """
        documentsDir = os.path.expanduser(self.config[args.lib]["dir"])
        self.logger.debug("Using directory %s" % documentsDir)
        documentSearch = args.document
        documents = papis.utils.get_documents_in_dir(
            documentsDir,
            documentSearch
        )
        document = self.pick(documents)
        if not document:
            sys.exit(0)
        folder = document.get_main_folder()
        if not args.force:
            if input("Are you sure? (Y/n): ") in ["N", "n"]:
                sys.exit(0)
        print("Removing %s..." % folder)
        shutil.rmtree(folder)
