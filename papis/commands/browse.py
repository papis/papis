import papis
import os
import sys
import papis.utils


class Browse(papis.commands.Command):
    def init(self):

        self.parser = self.get_subparsers().add_parser(
            "browse",
            help="Open document url if this exists"
        )

        self.add_search_argument()

    def main(self):
        documents = papis.utils.get_documents_in_lib(
            self.get_args().lib,
            self.get_args().search
        )
        document = self.pick(documents) or sys.exit(0)
        if "url" in document.keys():
            papis.utils.general_open(
                document["url"], "browser"
            )
        else:
            self.logger.warning(
                "No url for %s" % (document.get_main_folder_name())
            )
