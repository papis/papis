import sys
import os
import re
import papis.utils
import papis.config


class Gui(papis.commands.Command):
    def init(self):

        self.parser = self.get_subparsers().add_parser(
            "gui",
            help="Graphical user interface"
        )

        self.parser.add_argument(
            "--rofi",
            help="Rofi based gui",
            action="store_true"
        )

    def fetch_documents(self):
        return papis.utils.get_documents_in_lib(self.args.lib)

    def rofi_main(self):
        import papis.rofi
        return papis.rofi.Gui().main(self.documents)

    def main(self):
        self.documents = self.fetch_documents()
        return self.rofi_main()
