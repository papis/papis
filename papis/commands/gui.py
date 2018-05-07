import papis.utils
import papis.config


class Command(papis.commands.Command):
    def init(self):

        self.parser = self.get_subparsers().add_parser(
            "gui",
            help="Graphical user interface"
        )

        self.add_search_argument()

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
            "--urwid",
            help="Urwid based UI",
            action="store_true"
        )

        self.parser.add_argument(
            "--vim",
            help="Vim based UI",
            action="store_true"
        )

    def urwid_main(self):
        import papis.gui.urwid
        return papis.gui.urwid.Gui().main()

    def rofi_main(self):
        import papis.gui.rofi
        return papis.gui.rofi.Gui().main(self.documents)

    def tk_main(self):
        import papis.gui.tk
        return papis.gui.tk.Gui().main(self.documents)

    def vim_main(self):
        import papis.gui.vim
        return papis.gui.vim.Gui().main(self.documents, self.args)

    def main(self):
        self.documents = self.get_db().query(self.args.search)
        if self.args.tk:
            return self.tk_main()
        if self.args.urwid:
            return self.urwid_main()
        if self.args.vim:
            return self.vim_main()
        if self.args.rofi:
            return self.rofi_main()
        default = papis.config.get("default-gui")
        return exec("self.%s_main()" % default)
