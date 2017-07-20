import papis.utils
import papis.config


class Gui(papis.commands.Command):
    def init(self):

        self.parser = self.get_subparsers().add_parser(
            "gui",
            help="Graphical user interface"
        )

        self.parser.add_argument(
            "--tk",
            help="Tk based UI",
            action="store_true"
        )

        self.parser.add_argument(
            "--rofi",
            help="Rofi based UI",
            action="store_true"
        )

        self.parser.add_argument(
            "--vim",
            help="Vim based UI",
            action="store_true"
        )

    def fetch_documents(self):
        return papis.utils.get_documents_in_lib(self.args.lib)

    def rofi_main(self):
        import papis.gui.rofi
        return papis.gui.rofi.Gui().main(self.documents)

    def tk_main(self):
        import papis.gui.tk
        return papis.gui.tk.Gui().main(self.documents)

    def vim_main(self):
        import papis.gui.vim
        return papis.gui.vim.Gui().main(self.documents)

    def main(self):
        self.documents = self.fetch_documents()
        if self.args.tk:
            return self.tk_main()
        if self.args.vim:
            return self.vim_main()
        else:
            return self.rofi_main()
