import papis.utils
import papis.config
import papis.database
import papis.cli
import click


@click.command()
@click.help_option('--help', '-h')
@papis.cli.query_option()
@click.option(
    "--tk",
    help="Tk based UI",
    default=False,
    is_flag=True
)
@click.option(
    "--rofi",
    help="Rofi based UI",
    default=False,
    is_flag=True
)
@click.option(
    "--urwid",
    help="Urwid based UI",
    default=False,
    is_flag=True
)
@click.option(
    "--vim",
    help="Vim based UI",
    default=False,
    is_flag=True
)
def cli(query, tk, rofi, urwid, vim):
    """Graphical/Text user interface"""
    import papis.database

    documents = papis.database.get().query(query)
    default_gui = papis.config.get('default-gui')
    if not tk and not urwid and not vim and not rofi:
        if default_gui == 'tk': tk = True
        elif default_gui == 'urwid': urwid = True
        elif default_gui == 'vim': vim = True
        elif default_gui == 'rofi': rofi = True

    if tk:
        import papis.gui.tk
        return papis.gui.tk.Gui().main(documents)
    if urwid:
        import papis.gui.urwid
        return papis.gui.urwid.Gui().main()
    if vim:
        import papis.gui.vim
        return papis.gui.vim.Gui().main(documents, None)
    if rofi:
        import papis.gui.rofi
        return papis.gui.rofi.Gui().main(documents)
