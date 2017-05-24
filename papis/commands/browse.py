import webbrowser
import papis
import os
import papis.utils


class Browse(papis.commands.Command):
    def init(self):

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
        documentsDir = os.path.expanduser(self.config[self.args.lib]["dir"])
        self.logger.debug("Using directory %s" % documentsDir)
        documentSearch = self.args.document
        documents = papis.utils.get_documents_in_dir(
            documentsDir,
            documentSearch
        )
        document = self.pick(documents)
        if "url" in document.keys():
            papis.utils.general_open(document["url"], "BROWSER", webbrowser.open)
        else:
            self.logger.warning(
                "No url for %s" % (document.get_main_folder_name())
            )
