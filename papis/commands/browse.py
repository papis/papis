import webbrowser
import papis
import os
import papis.utils


class Browse(papis.commands.Command):
    def init(self):
        """TODO: Docstring for init.

        :subparser: TODO
        :returns: TODO

        """

        # open parser
        self.parser = self.get_subparsers().add_parser(
            "browse",
            help="Open document url if this exists"
        )
        self.parser.add_argument(
            "document",
            help="Document search",
            nargs="?",
            default=".",
            action="store"
        )

    def main(self):
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
        if "url" in document.keys():
            webbrowser.open(document["url"])
        else:
            self.logger.warning(
                "No url for %s" % (document.get_main_folder_name())
            )
