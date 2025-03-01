import threading
from functools import partial

from prompt_toolkit.application import Application
from prompt_toolkit.formatted_text.html import HTML
from prompt_toolkit.enums import EditingMode
from prompt_toolkit.layout.processors import BeforeInput
from prompt_toolkit.key_binding import KeyBindings, KeyPressEvent, merge_key_bindings
from prompt_toolkit.filters import has_focus, Condition
from prompt_toolkit.styles import Style
from prompt_toolkit.layout.containers import (
    HSplit, Window
)
from prompt_toolkit.layout.controls import (
    BufferControl,
)
from prompt_toolkit.layout.layout import Layout

from papis import config
from .widgets.command_line_prompt import Command, CommandLinePrompt
from .widgets import InfoWindow, HelpWindow, MessageToolbar
from .widgets.list import Option, OptionsList

from typing import (
    Optional, Dict, Any, List, Callable, Tuple, Generic,
    Sequence, TypedDict, Union)

__all__ = [
    "Option",
    "Picker"
]


class KeyInfo(TypedDict):
    key: str
    help: str


_KEYS_INFO: Optional[Dict[str, KeyInfo]] = None


def get_keys_info() -> Dict[str, KeyInfo]:
    global _KEYS_INFO
    if _KEYS_INFO is None:
        _KEYS_INFO = {
            "move_down_key": {
                "key": config.getstring("move_down_key", section="tui"),
                "help": "Move cursor down in the list",
            },
            "move_up_key": {
                "key": config.getstring("move_up_key", section="tui"),
                "help": "Move cursor up in the list",
            },
            "move_down_while_info_window_active_key": {
                "key": config.getstring(
                    "move_down_while_info_window_active_key", section="tui"
                ),
                "help": "Move cursor down while info window is active",
            },
            "move_up_while_info_window_active_key": {
                "key": config.getstring(
                    "move_up_while_info_window_active_key", section="tui"
                ),
                "help": "Move cursor up while info window is active",
            },
            "focus_command_line_key": {
                "key":
                    config.getstring("focus_command_line_key", section="tui"),
                "help": "Focus command line prompt",
            },
            "browse_document_key": {
                "key": config.getstring("browse_document_key", section="tui"),
                "help": "Browse currently selected document",
            },
            "edit_document_key": {
                "key": config.getstring("edit_document_key", section="tui"),
                "help": "Edit currently selected document",
            },
            "edit_notes_key": {
                "key": config.getstring("edit_notes_key", section="tui"),
                "help": "Edit notes of currently selected document",
            },
            "open_document_key": {
                "key": config.getstring("open_document_key", section="tui"),
                "help": "Open currently selected document",
            },
            "show_help_key": {
                "key": config.getstring("show_help_key", section="tui"),
                "help": "Show help",
            },
            "show_info_key": {
                "key": config.getstring("show_info_key", section="tui"),
                "help": "Show the yaml information of the current document",
            },
            "go_top_key": {
                "key": config.getstring("go_top_key", section="tui"),
                "help": "Go to the top of the list",
            },
            "go_bottom_key": {
                "key": config.getstring("go_bottom_key", section="tui"),
                "help": "Go to the bottom of the list",
            },
            "mark_key": {
                "key": config.getstring("mark_key", section="tui"),
                "help": "Mark current item to be selected",
            },
        }
    return _KEYS_INFO


def create_keybindings(app: "Picker[Any]") -> KeyBindings:
    keys_info = get_keys_info()
    kb = KeyBindings()

    @kb.add("escape",
            filter=Condition(lambda: app.message_toolbar.text))
    def _escape_message(event: KeyPressEvent) -> None:
        app.message_toolbar.text = None

    @kb.add("escape",
            filter=Condition(lambda: app.error_toolbar.text))
    def _escape_error(event: KeyPressEvent) -> None:
        app.error_toolbar.text = None

    @kb.add("c-n",                                      # type: ignore[misc]
            filter=~has_focus(app.info_window))
    @kb.add(str(keys_info["move_down_key"]["key"]),     # type: ignore[misc]
            filter=~has_focus(app.info_window))
    def _down(event: KeyPressEvent) -> None:
        app.options_list.move_down()
        app.refresh()
        app.update()

    @kb.add(                                            # type: ignore[misc]
        keys_info["move_down_while_info_window_active_key"]["key"],
        filter=has_focus(app.info_window))
    def _down_info(event: KeyPressEvent) -> None:
        _down(event)
        app.update_info_window()

    @kb.add("c-p",                                      # type: ignore[misc]
            filter=~has_focus(app.info_window))
    @kb.add(keys_info["move_up_key"]["key"],            # type: ignore[misc]
            filter=~has_focus(app.info_window))
    def _up(event: KeyPressEvent) -> None:
        app.options_list.move_up()
        app.refresh()
        app.update()

    @kb.add(                                            # type: ignore[misc]
        keys_info["move_up_while_info_window_active_key"]["key"],
        filter=has_focus(app.info_window))
    def _up_info(event: KeyPressEvent) -> None:
        _up(event)
        app.update_info_window()

    @kb.add("q",                                        # type: ignore[misc]
            filter=has_focus(app.help_window))
    @kb.add("escape",                                   # type: ignore[misc]
            filter=has_focus(app.help_window))
    def _help_quit(event: KeyPressEvent) -> None:
        app.layout.focus(app.help_window.window)
        app.layout.focus(app.command_line_prompt.window)
        app.message_toolbar.text = None
        app.layout.focus(app.options_list.search_buffer)

    @kb.add("q",                                        # type: ignore[misc]
            filter=has_focus(app.info_window))
    @kb.add("s-tab",                                    # type: ignore[misc]
            filter=has_focus(app.info_window))
    @kb.add("escape",                                   # type: ignore[misc]
            filter=has_focus(app.info_window))
    def _info(event: KeyPressEvent) -> None:
        app.layout.focus(app.options_list.search_buffer)
        app.message_toolbar.text = None

    @kb.add(                                            # type: ignore[misc]
        keys_info["focus_command_line_key"]["key"],
        filter=~has_focus(app.command_line_prompt))
    def _command_window(event: KeyPressEvent) -> None:
        app.layout.focus(app.command_line_prompt.window)

    @kb.add("enter",                                    # type: ignore[misc]
            filter=has_focus(app.command_line_prompt))
    def _enter(event: KeyPressEvent) -> None:
        app.layout.focus(app.options_list.search_buffer)
        try:
            app.command_line_prompt.trigger()
        except Exception as e:
            app.error_toolbar.text = str(e)
        app.command_line_prompt.clear()

    @kb.add("escape",                                   # type: ignore[misc]
            filter=has_focus(app.command_line_prompt))
    def _escape_when_commandline_has_focus(event: KeyPressEvent) -> None:
        app.layout.focus(app.options_list.search_buffer)
        app.command_line_prompt.clear()

    @kb.add("c-t")
    def _toggle_mark_(event: KeyPressEvent) -> None:
        app.options_list.toggle_mark_current_selection()

    return kb


def get_commands(app: "Picker[Any]") -> Tuple[List[Command], KeyBindings]:
    kb = KeyBindings()
    keys_info = get_keys_info()

    @kb.add("c-q")
    @kb.add("c-c")
    def exit(event: Union[Command, KeyPressEvent]) -> None:
        app.deselect()
        app.exit()

    @kb.add("enter",                                    # type: ignore[misc]
            filter=has_focus(app.options_list.search_buffer))
    def select(event: Union[Command, KeyPressEvent]) -> None:
        app.exit()

    @kb.add(keys_info["open_document_key"]["key"],      # type: ignore[misc]
            filter=has_focus(app.options_list.search_buffer))
    def open(event: Union[Command, KeyPressEvent]) -> None:
        from papis.commands.open import run

        docs = app.get_selection()
        for doc in docs:
            # NOTE: `run` can spawn another picker if the document has more files
            # but prompt_toolkit does not support multiple event loops at the same
            # time. To get around this, we run it in a thread!
            # Inspired by: https://github.com/ipython/ipython/pull/12141
            thread = threading.Thread(target=partial(run, doc))
            thread.start()
            thread.join()

        app.renderer.clear()

    @kb.add(keys_info["browse_document_key"]["key"],      # type: ignore[misc]
            filter=has_focus(app.options_list.search_buffer))
    def browse(event: Union[Command, KeyPressEvent]) -> None:
        from papis.commands.browse import run
        docs = app.get_selection()
        for doc in docs:
            run(doc)

    @kb.add(keys_info["edit_document_key"]["key"],      # type: ignore[misc]
            filter=has_focus(app.options_list.search_buffer))
    def edit(event: Union[Command, KeyPressEvent]) -> None:
        from papis.commands.edit import run
        docs = app.get_selection()
        for doc in docs:
            run(doc)

    @kb.add(keys_info["edit_notes_key"]["key"],         # type: ignore[misc]
            filter=has_focus(app.options_list.search_buffer))
    def edit_notes(event: KeyPressEvent) -> None:
        from papis.commands.edit import edit_notes
        docs = app.get_selection()
        for doc in docs:
            edit_notes(doc)
        app.renderer.clear()

    @kb.add(keys_info["show_help_key"]["key"],          # type: ignore[misc]
            filter=~has_focus(app.help_window))
    def help(event: Union[Command, KeyPressEvent]) -> None:
        app.layout.focus(app.help_window.window)
        app.message_toolbar.text = "Press q to quit"

    @kb.add(keys_info["show_info_key"]["key"],          # type: ignore[misc]
            filter=~has_focus(app.info_window))
    def info(event: Union[Command, KeyPressEvent]) -> None:
        app.update_info_window()
        app.layout.focus(app.info_window.window)

    @kb.add("c-g", "g")
    @kb.add(keys_info["go_top_key"]["key"])
    def go_top(event: Union[Command, KeyPressEvent]) -> None:
        app.options_list.go_top()
        app.refresh()

    @kb.add("c-g", "G")
    @kb.add(keys_info["go_bottom_key"]["key"])
    def go_end(event: Union[Command, KeyPressEvent]) -> None:
        app.options_list.go_bottom()
        app.refresh()

    return ([
        Command("open", run=open, aliases=["op"]),
        Command("edit", run=edit, aliases=["e"]),
        Command("select", run=select, aliases=["e"]),
        Command("exit", run=exit, aliases=["quit", "q"]),
        Command("info", run=info, aliases=["i"]),
        Command("go_top", run=go_top),
        Command("go_bottom", run=go_end),
        Command("move_down", run=lambda c: app.options_list.move_down()),
        Command("move_up", run=lambda c: app.options_list.move_up()),
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
            match_filter: Callable[[Option], str] = str) -> None:

        self.info_window = InfoWindow()
        self.help_window = HelpWindow()
        self.message_toolbar = MessageToolbar(style="class:message_toolbar")
        self.error_toolbar = MessageToolbar(style="class:error_toolbar")
        self.status_line = MessageToolbar(style="class:status_line")
        self.status_line_format = config.getstring(
            "status_line_format", section="tui")

        self.options_list = OptionsList(
            options,
            default_index,
            header_filter=header_filter,
            match_filter=match_filter,
            custom_filter=~has_focus(self.help_window)
        )
        self.options_list.search_buffer.on_text_changed += self.update

        commands, commands_kb = get_commands(self)
        self.command_line_prompt = CommandLinePrompt(commands=commands)
        kb = merge_key_bindings([create_keybindings(self), commands_kb])

        root_container = HSplit([
            HSplit([
                Window(
                    content=BufferControl(
                        input_processors=[BeforeInput("> ")],
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

        help_text = ""
        keys_info = get_keys_info()
        for k in keys_info:
            help_text += (
                "<ansired>{}</ansired>: {}\n"
                .format(keys_info[k]["key"], keys_info[k]["help"])
            )
        self.help_window.text = HTML(help_text)

        self.layout = Layout(root_container)

        super().__init__(
            input=None,
            output=None,
            editing_mode=EditingMode.EMACS
            if config.get("editmode", section="tui") == "emacs"
            else EditingMode.VI,
            layout=self.layout,
            style=Style.from_dict({
                "options_list.selected_margin": config.getstring(
                    "options_list.selected_margin_style", section="tui"
                ),
                "options_list.unselected_margin": config.getstring(
                    "options_list.unselected_margin_style", section="tui"
                ),
                "options_list.marked_margin": config.getstring(
                    "options_list.marked_margin_style", section="tui"
                ),
                "error_toolbar": config.getstring(
                    "error_toolbar_style", section="tui"
                ),
                "message_toolbar": config.getstring(
                    "message_toolbar_style", section="tui"
                ),
                "status_line": config.getstring(
                    "status_line_style", section="tui"
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
