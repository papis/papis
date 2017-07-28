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
        documents = papis.utils.get_documents_in_lib(
            self.get_args().lib,
            self.get_args().document
        )
        document = self.pick(documents)
        if "url" in document.keys():
            papis.utils.general_open(
                document["url"], "browser"
            )
        else:
            self.logger.warning(
                "No url for %s" % (document.get_main_folder_name())
            )
