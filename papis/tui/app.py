from prompt_toolkit.utils import Event
from prompt_toolkit.application import Application
from prompt_toolkit.formatted_text.html import HTML
from prompt_toolkit.enums import EditingMode
from prompt_toolkit.layout.processors import BeforeInput
from prompt_toolkit.key_binding import KeyBindings, merge_key_bindings
from prompt_toolkit.filters import has_focus, Condition
from prompt_toolkit.styles import Style
from prompt_toolkit.layout.containers import (
    HSplit, Window
)
from prompt_toolkit.layout.controls import (
    BufferControl,
)
from prompt_toolkit.layout.layout import Layout
import papis.config as config

from .widgets.command_line_prompt import Command, CommandLinePrompt
from .widgets import InfoWindow, HelpWindow, MessageToolbar
from .widgets.list import Option, OptionsList

from typing import (  # noqa: ignore
    Optional, Dict, Any, List, Callable, Tuple, Generic,
    Sequence)
from typing_extensions import TypedDict

__all__ = [
    "Option",
    "Picker"
]

KeyInfo = TypedDict("KeyInfo", {"key": str, "help": str})

_KEYS_INFO = None  # type: Optional[Dict[str, KeyInfo]]


def get_keys_info() -> Dict[str, KeyInfo]:
    global _KEYS_INFO
    if _KEYS_INFO is None:
        _KEYS_INFO = {
            "move_down_key": {
                'key': config.getstring('move_down_key', section='tui'),
                'help': 'Move cursor down in the list',
            },
            "move_up_key": {
                'key': config.getstring('move_up_key', section='tui'),
                'help': 'Move cursor up in the list',
            },
            "move_down_while_info_window_active_key": {
                'key': config.getstring(
                    'move_down_while_info_window_active_key', section='tui'
                ),
                'help': 'Move cursor down while info window is active',
            },
            "move_up_while_info_window_active_key": {
                'key': config.getstring(
                    'move_up_while_info_window_active_key', section='tui'
                ),
                'help': 'Move cursor up while info window is active',
            },
            "focus_command_line_key": {
                'key':
                    config.getstring('focus_command_line_key', section='tui'),
                'help': 'Focus command line prompt',
            },
            "edit_document_key": {
                'key': config.getstring('edit_document_key', section='tui'),
                'help': 'Edit currently selected document',
            },
            "open_document_key": {
                'key': config.getstring('open_document_key', section='tui'),
                'help': 'Open currently selected document',
            },
            "show_help_key": {
                'key': config.getstring('show_help_key', section='tui'),
                'help': 'Show help',
            },
            "show_info_key": {
                'key': config.getstring('show_info_key', section='tui'),
                'help': 'Show the yaml information of the current document',
            },
            "go_top_key": {
                'key': config.getstring('go_top_key', section='tui'),
                'help': 'Go to the top of the list',
            },
            "go_bottom_key": {
                'key': config.getstring('go_bottom_key', section='tui'),
                'help': 'Go to the bottom of the list',
            },
        }
    return _KEYS_INFO


def create_keybindings(app: Application) -> KeyBindings:
    keys_info = get_keys_info()
    kb = KeyBindings()

    @kb.add('escape',  # type: ignore
            filter=Condition(lambda: app.message_toolbar.text))
    def _(event: Event) -> None:
        event.app.message_toolbar.text = None

    @kb.add('escape',  # type: ignore
            filter=Condition(lambda: app.error_toolbar.text))
    def _escape(event: Event) -> None:
        event.app.error_toolbar.text = None

    @kb.add('c-n', filter=~has_focus(app.info_window))  # type: ignore
    @kb.add(keys_info["move_down_key"]["key"],  # type: ignore
            filter=~has_focus(app.info_window))
    def down_(event: Event) -> None:
        event.app.options_list.move_down()
        event.app.refresh()
        event.app.update()

    @kb.add(  # type: ignore
        keys_info["move_down_while_info_window_active_key"]["key"],
        filter=has_focus(app.info_window))
    def down_info(event: Event) -> None:
        down_(event)
        event.app.update_info_window()

    @kb.add('c-p', filter=~has_focus(app.info_window))  # type: ignore
    @kb.add(keys_info["move_up_key"]["key"],  # type: ignore
            filter=~has_focus(app.info_window))
    def up_(event: Event) -> None:
        event.app.options_list.move_up()
        event.app.refresh()
        event.app.update()

    @kb.add(  # type: ignore
        keys_info["move_up_while_info_window_active_key"]["key"],
        filter=has_focus(app.info_window))
    def up_info(event: Event) -> None:
        up_(event)
        event.app.update_info_window()

    @kb.add('q', filter=has_focus(app.help_window))  # type: ignore
    @kb.add('escape', filter=has_focus(app.help_window))  # type: ignore
    def _help_quit(event: Event) -> None:
        event.app.layout.focus(app.help_window.window)
        event.app.layout.focus(app.command_line_prompt.window)
        event.app.message_toolbar.text = None
        event.app.layout.focus(event.app.options_list.search_buffer)

    @kb.add('q', filter=has_focus(app.info_window))  # type: ignore
    @kb.add('s-tab', filter=has_focus(app.info_window))  # type: ignore
    @kb.add('escape', filter=has_focus(app.info_window))  # type: ignore
    def _info(event: Event) -> None:
        event.app.layout.focus(event.app.options_list.search_buffer)
        event.app.message_toolbar.text = None

    @kb.add(keys_info["focus_command_line_key"]["key"],  # type: ignore
            filter=~has_focus(app.command_line_prompt))
    def _command_window(event: Event) -> None:
        event.app.layout.focus(app.command_line_prompt.window)

    @kb.add('enter', filter=has_focus(app.command_line_prompt))  # type: ignore
    def _enter_(event: Event) -> None:
        event.app.layout.focus(event.app.options_list.search_buffer)
        try:
            event.app.command_line_prompt.trigger()
        except Exception as e:
            event.app.error_toolbar.text = str(e)
        event.app.command_line_prompt.clear()

    @kb.add('escape',  # type: ignore
            filter=has_focus(app.command_line_prompt))
    def _escape_when_commandline_has_focus(event: Event) -> None:
        event.app.layout.focus(event.app.options_list.search_buffer)
        event.app.command_line_prompt.clear()

    @kb.add('c-t')  # type: ignore
    def _toggle_mark_(event: Event) -> None:
        event.app.options_list.toggle_mark_current_selection()

    return kb


def get_commands(app: Application) -> Tuple[List[Command], KeyBindings]:

    kb = KeyBindings()
    keys_info = get_keys_info()

    @kb.add('c-q')  # type: ignore
    @kb.add('c-c')  # type: ignore
    def exit(event: Event) -> None:
        event.app.deselect()
        event.app.exit()

    @kb.add('enter',  # type: ignore
            filter=has_focus(app.options_list.search_buffer))
    def select(event: Event) -> None:
        event.app.exit()

    @kb.add(keys_info["open_document_key"]["key"],  # type: ignore
            filter=has_focus(app.options_list.search_buffer))
    def open(cmd: Command) -> None:
        from papis.commands.open import run
        docs = cmd.app.get_selection()
        for doc in docs:
            run(doc)

    @kb.add(keys_info["edit_document_key"]["key"],  # type: ignore
            filter=has_focus(app.options_list.search_buffer))
    def edit(cmd: Command) -> None:
        from papis.commands.edit import run
        docs = cmd.app.get_selection()
        for doc in docs:
            run(doc)
        cmd.app.renderer.clear()

    @kb.add(keys_info["show_help_key"]["key"],  # type: ignore
            filter=~has_focus(app.help_window))
    def help(event: Event) -> None:
        event.app.layout.focus(app.help_window.window)
        event.app.message_toolbar.text = 'Press q to quit'

    # def _echo(cmd, *args) -> None:
        # cmd.app.message_toolbar.text = ' '.join(args)

    @kb.add(keys_info["show_info_key"]["key"],  # type: ignore
            filter=~has_focus(app.info_window))
    def info(cmd: Command) -> None:
        cmd.app.update_info_window()
        cmd.app.layout.focus(cmd.app.info_window.window)

    @kb.add('c-g', 'g')  # type: ignore
    @kb.add(keys_info["go_top_key"]["key"])  # type: ignore
    def go_top(event: Event) -> None:
        event.app.options_list.go_top()
        event.app.refresh()

    @kb.add('c-g', 'G')  # type: ignore
    @kb.add(keys_info["go_bottom_key"]["key"])  # type: ignore
    def go_end(event: Event) -> None:
        event.app.options_list.go_bottom()
        event.app.refresh()

    return ([
        Command("open", run=open, aliases=["op"]),
        Command("edit", run=edit, aliases=["e"]),
        Command("select", run=select, aliases=["e"]),
        Command("exit", run=exit, aliases=["quit", "q"]),
        Command("info", run=info, aliases=["i"]),
        Command("go_top", run=go_top),
        Command("go_bottom", run=go_end),
        Command("move_down", run=lambda c: c.app.options_list.move_down()),
        Command("move_up", run=lambda c: c.app.options_list.move_up()),
        # Command("echo", run=_echo),
        Command("help", run=help),
    ], kb)


class Picker(Application, Generic[Option]):  # type: ignore
    """The :class:`Picker <Picker>` object

    :param options: a list of options to choose from
    :param default_index: (optional) set this if the default
        selected option is not the first one
    """

    def __init__(
            self,
            options: Sequence[Option],
            default_index: int = 0,
            header_filter: Callable[[Option], str] = str,
            match_filter: Callable[[Option], str] = str):

        self.info_window = InfoWindow()
        self.help_window = HelpWindow()
        self.message_toolbar = MessageToolbar(style="class:message_toolbar")
        self.error_toolbar = MessageToolbar(style="class:error_toolbar")
        self.status_line = MessageToolbar(style="class:status_line")
        self.status_line_format = config.getstring(
            'status_line_format', section="tui")

        self.options_list = OptionsList(
            options,
            default_index,
            header_filter=header_filter,
            match_filter=match_filter,
            custom_filter=~has_focus(self.help_window)
        )  # type: OptionsList[Option]
        self.options_list.search_buffer.on_text_changed += self.update

        commands, commands_kb = get_commands(self)
        self.command_line_prompt = CommandLinePrompt(commands=commands)
        kb = merge_key_bindings([create_keybindings(self), commands_kb])

        _root_container = HSplit([
            HSplit([
                Window(
                    content=BufferControl(
                        input_processors=[BeforeInput('> ')],
                        buffer=self.options_list.search_buffer
                    )
                ),
                self.options_list,
                self.info_window,
            ]),
            self.help_window,
            self.error_toolbar,
            self.message_toolbar,
            self.status_line,
            self.command_line_prompt.window,
        ])

        help_text = ""  # type: str
        keys_info = get_keys_info()
        for k in keys_info:
            help_text += (
                "<ansired>{k[key]}</ansired>: {k[help]}\n".format(
                    k=keys_info[k]
                )
            )
        self.help_window.text = HTML(help_text)

        self.layout = Layout(_root_container)

        super(Picker, self).__init__(
            input=None,
            output=None,
            editing_mode=EditingMode.EMACS
            if config.get('editmode', section='tui') == 'emacs'
            else EditingMode.VI,
            layout=self.layout,
            style=Style.from_dict({
                'options_list.selected_margin': config.get(
                    'options_list.selected_margin_style', section='tui'
                ),
                'options_list.unselected_margin': config.get(
                    'options_list.unselected_margin_style', section='tui'
                ),
                'error_toolbar': config.get(
                    'error_toolbar_style', section='tui'
                ),
                'message_toolbar': config.get(
                    'message_toolbar_style', section='tui'
                ),
                'status_line': config.get(
                    'status_line_style', section='tui'
                ),
            }),
            key_bindings=kb,
            include_default_pygments_style=False,
            full_screen=True,
            enable_page_navigation_bindings=True
        )
        self.update()

    def deselect(self) -> None:
        self.options_list.deselect()

    def refresh_status_line(self) -> None:
        if self.options_list.current_index is not None:
            self.status_line.text = self.status_line_format.format(
                selected_index=int(self.options_list.current_index) + 1,
                number_of_documents=len(self.options_list.get_options()),)

    def refresh(self, *args: Any) -> None:
        self.refresh_status_line()

    def update(self, *args: Any) -> None:
        self.options_list.update()
        self.refresh_status_line()

    def get_selection(self) -> Sequence[Option]:
        return self.options_list.get_selection()

    def update_info_window(self) -> None:
        doc = self.options_list.get_selection()
        self.info_window.text = str(doc)
