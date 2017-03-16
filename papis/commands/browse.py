import webbrowser
from ..document import Document
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
        open_parser = self.parser.add_parser(
                "browse",
                help="Open document url if this exists"
                )
        open_parser.add_argument(
                "document",
                help="Document search",
                nargs="?",
                default=".",
                action="store"
                )

    def main(self, config, args):
        """
        Main action if the command is triggered

        :config: User configuration
        :args: CLI user arguments
        :returns: TODO

        """
        documentsDir = os.path.expanduser(config[args.lib]["dir"])
        self.logger.debug("Using directory %s" % documentsDir)
        documentSearch = args.document
        folders = papis.utils.getFilteredFolders(documentsDir, documentSearch)
        folder = self.pick(folders, config, strip=documentsDir)
        document = Document(folder)
        if "url" in document.keys():
            webbrowser.open(document["url"])
        else:
            self.logger.warning("No url for %s" % (os.path.basename(folder)))
