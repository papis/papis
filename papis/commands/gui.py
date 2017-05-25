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
        import rofi
        import papis.rofi
        # Set default picker
        key = None
        index = None
        options = papis.rofi.get_options()
        header_format = papis.config.get_header_format()
        header_filter = lambda x: header_format.format(doc=x)
        esc_key = -1
        quit_key = 1
        edit_key = 2
        delete_key = 3
        open_key = 0
        keys = {
            "key%s" % quit_key: ('Alt+q', 'Quit'),
            "key%s" % edit_key: ('Alt+e', 'Edit'),
            "key%s" % delete_key: ('Alt+d', 'Delete'),
            "key%s" % open_key: ('Enter', 'Open')
        }
        options.update(keys)
        # Initialize window
        w = rofi.Rofi()
        while not (key == quit_key or key == esc_key):
            index, key = w.select( "Select: ",
                [
                    header_filter(d) for d in
                    self.documents
                ],
                select=index,
                **options
            )
            if key == edit_key:
                papis.utils.general_open(
                    self.documents[index].get_info_file(),
                    "xeditor",
                    default_opener="xterm -e vim",
                    wait=True
                )
            elif key == open_key:
                return papis.utils.open_file(
                    self.documents[index].get_files()
                )
            elif key == delete_key:
                answer = w.text_entry("Are you sure? <b>(y/N)</b>")
                if answer in "Yy":
                    self.documents[index].rm()
                    self.documents = self.fetch_documents()

    def main(self):
        self.documents = self.fetch_documents()
        self.rofi_main()
