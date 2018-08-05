import papis.utils
import papis.config
import papis.database
import papis.cli
import click


@click.command()
@click.help_option('--help', '-h')
@papis.cli.query_option()
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
def cli(query, urwid, vim):
    """Graphical/Text user interface"""
    import papis.database

    documents = papis.database.get().query(query)
    default_gui = papis.config.get('default-gui')
    if not urwid and not vim:
        if default_gui == 'urwid':
            urwid = True
        elif default_gui == 'vim':
            vim = True

    if urwid:
        import papis.gui.urwid
        return papis.gui.urwid.Gui().main()
    if vim:
        import papis.gui.vim
        return papis.gui.vim.Gui().main(documents, None)
