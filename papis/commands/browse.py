import webbrowser
import papis
import os
import papis.utils
from . import Command


class Browse(Command):
    def init(self):
        """TODO: Docstring for init.

        :subparser: TODO
        :returns: TODO

        """

        # open parser
        self.subparser = self.parser.add_parser(
            "browse",
            help="Open document url if this exists"
        )
        self.subparser.add_argument(
            "document",
            help="Document search",
            nargs="?",
            default=".",
            action="store"
        )

    def main(self, args):
        """
        Main action if the command is triggered

        :config: User configuration
        :args: CLI user arguments
        :returns: TODO

        """
        documentsDir = os.path.expanduser(config[args.lib]["dir"])
        self.logger.debug("Using directory %s" % documentsDir)
        documentSearch = args.document
        documents = papis.utils.getFilteredDocuments(
            documentsDir,
            documentSearch
        )
        document = self.pick(documents, config)
        if "url" in document.keys():
            webbrowser.open(document["url"])
        else:
            self.logger.warning(
                "No url for %s" % (document.getMainFolderName())
            )
