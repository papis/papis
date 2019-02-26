import os
import re
from prompt_toolkit.application import Application
from prompt_toolkit.formatted_text.html import HTML
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.enums import EditingMode
from prompt_toolkit.layout.processors import BeforeInput
from prompt_toolkit.key_binding import KeyBindings, merge_key_bindings
from prompt_toolkit.layout.screen import Point
from prompt_toolkit.filters import has_focus, Condition
from prompt_toolkit.styles import Style
from prompt_toolkit.layout.containers import (
    HSplit, Window, ConditionalContainer
)
from prompt_toolkit.layout.controls import (
    BufferControl,
)
from prompt_toolkit.layout.layout import Layout
import papis.config as config
import logging

from .widgets.command_line_prompt import Command
from .widgets import (
    InfoWindow, CommandLinePrompt, HelpWindow, OptionsList,
    MessageToolbar
)

logger = logging.getLogger('pick')

_keys_info = None
def get_keys_info():
    global _keys_info
    if not _keys_info:
        _keys_info = {
            "move_down_key": {
                'key': config.get('move_down_key', section='tui'),
                'help': 'Move cursor down in the list',
            },
            "move_up_key": {
                'key': config.get('move_up_key', section='tui'),
                'help': 'Move cursor up in the list',
            },
            "move_down_while_info_window_active_key": {
                'key': config.get('move_down_while_info_window_active_key', section='tui'),
                'help': 'Move cursor down while info window is active',
            },
            "move_up_while_info_window_active_key": {
                'key': config.get('move_up_while_info_window_active_key', section='tui'),
                'help': 'Move cursor up while info window is active',
            },
            "focus_command_line_key": {
                'key': config.get('focus_command_line_key', section='tui'),
                'help': 'Focus command line prompt',
            },
            "edit_document_key": {
                'key': config.get('edit_document_key', section='tui'),
                'help': 'Edit currently selected document',
            },
            "open_document_key": {
                'key': config.get('open_document_key', section='tui'),
                'help': 'Open currently selected document',
            },
            "show_help_key": {
                'key': config.get('show_help_key', section='tui'),
                'help': 'Show help',
            },
            "show_info_key": {
                'key': config.get('show_info_key', section='tui'),
                'help': 'Show the yaml information of the current document',
            },
            "go_top_key": {
                'key': config.get('go_top_key', section='tui'),
                'help': 'Go to the top of the list',
            },
            "go_bottom_key": {
                'key': config.get('go_bottom_key', section='tui'),
                'help': 'Go to the bottom of the list',
            },
        }
    return _keys_info


def create_keybindings(app):
    keys_info = get_keys_info()
    kb = KeyBindings()

    @kb.add('escape', filter=Condition(lambda: app.message_toolbar.text))
    def _(event):
        event.app.message_toolbar.text = None

    @kb.add('escape', filter=Condition(lambda: app.error_toolbar.text))
    def _(event):
        event.app.error_toolbar.text = None

    @kb.add('c-n', filter=~has_focus(app.info_window))
    @kb.add(keys_info["move_down_key"]["key"], filter=~has_focus(app.info_window))
    def down_(event):
        event.app.options_list.move_down()
        event.app.refresh()
        event.app.update()

    @kb.add(
        keys_info["move_down_while_info_window_active_key"]["key"],
        filter=has_focus(app.info_window)
    )
    def down_info(event):
        down_(event)
        event.app.update_info_window()

    @kb.add('c-p', filter=~has_focus(app.info_window))
    @kb.add(keys_info["move_up_key"]["key"], filter=~has_focus(app.info_window))
    def up_(event):
        event.app.options_list.move_up()
        event.app.refresh()
        event.app.update()

    @kb.add(
        keys_info["move_up_while_info_window_active_key"]["key"],
        filter=has_focus(app.info_window)
    )
    def up_info(event):
        up_(event)
        event.app.update_info_window()

    @kb.add('q', filter=has_focus(app.help_window))
    @kb.add('escape', filter=has_focus(app.help_window))
    def _help_quit(event):
        event.app.layout.focus(app.help_window.window)
        event.app.layout.focus(app.command_line_prompt.window)
        event.app.message_toolbar.text = None
        event.app.layout.focus(event.app.options_list.search_buffer)

    @kb.add('q', filter=has_focus(app.info_window))
    @kb.add('s-tab', filter=has_focus(app.info_window))
    @kb.add('escape', filter=has_focus(app.info_window))
    def _info(event):
        event.app.layout.focus(event.app.options_list.search_buffer)
        event.app.message_toolbar.text = None

    @kb.add(
        keys_info["focus_command_line_key"]["key"],
        filter=~has_focus(app.command_line_prompt)
    )
    def _command_window(event):
        event.app.layout.focus(app.command_line_prompt.window)

    @kb.add('enter', filter=has_focus(app.command_line_prompt))
    def _enter_(event):
        event.app.layout.focus(event.app.options_list.search_buffer)
        try:
            event.app.command_line_prompt.trigger()
        except Exception as e:
            event.app.error_toolbar.text = str(e)
        event.app.command_line_prompt.clear()

    @kb.add('escape', filter=has_focus(app.command_line_prompt))
    def _(event):
        event.app.layout.focus(event.app.options_list.search_buffer)
        event.app.command_line_prompt.clear()

    return kb


def get_commands(app):

    kb = KeyBindings()
    keys_info = get_keys_info()

    @kb.add('c-q')
    @kb.add('c-c')
    def exit(event):
        event.app.deselect()
        event.app.exit()

    @kb.add(
        'enter',
        filter=has_focus(app.options_list.search_buffer)
    )
    def select(event):
        event.app.exit()

    @kb.add(
        keys_info["open_document_key"]["key"],
        filter=has_focus(app.options_list.search_buffer)
    )
    def open(cmd):
        from papis.commands.open import run
        doc = cmd.app.get_selection()
        run(doc)

    @kb.add(
        keys_info["edit_document_key"]["key"],
        filter=has_focus(app.options_list.search_buffer)
    )
    def edit(cmd):
        from papis.commands.edit import run
        doc = cmd.app.get_selection()
        run(doc)
        cmd.app.renderer.clear()

    @kb.add(
        keys_info["show_help_key"]["key"],
        filter=~has_focus(app.help_window)
    )
    def help(event):
        event.app.layout.focus(app.help_window.window)
        event.app.message_toolbar.text = 'Press q to quit'

    def _echo(cmd, *args):
        cmd.app.message_toolbar.text = ' '.join(args)

    @kb.add(
        keys_info["show_info_key"]["key"],
        filter=~has_focus(app.info_window)
    )
    def info(cmd):
        cmd.app.update_info_window()
        cmd.app.layout.focus(cmd.app.info_window.window)

    @kb.add('c-g', 'g')
    @kb.add(keys_info["go_top_key"]["key"])
    def go_top(event):
        event.app.options_list.go_top()
        event.app.refresh()

    @kb.add('c-g', 'G')
    @kb.add(keys_info["go_bottom_key"]["key"])
    def go_end(event):
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
        Command("echo", run=_echo),
        Command("help", run=help),
    ], kb)


class Picker(Application):
    """The :class:`Picker <Picker>` object

    :param options: a list of options to choose from
    :param default_index: (optional) set this if the default
        selected option is not the first one
    """

    def __init__(
            self,
            options,
            default_index=0,
            header_filter=lambda x: x,
            match_filter=lambda x: x
            ):


        self.info_window = InfoWindow()
        self.help_window = HelpWindow()
        self.message_toolbar = MessageToolbar(style="class:message_toolbar")
        self.error_toolbar = MessageToolbar(style="class:error_toolbar")
        self.status_line = MessageToolbar(style="class:status_line")
        self.status_line_format = config.get(
            'status_line_format', section="tui"
        )

        self.options_list = OptionsList(
            options,
            default_index,
            header_filter,
            match_filter,
            custom_filter=~has_focus(self.help_window)
        )

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

        regex = re.compile(r'.*\.([^ ]+) +at.*')

        help_text = ""
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

    def deselect(self):
        self.options_list.current_index = None

    def refresh_status_line(self):
        self.status_line.text = self.status_line_format.format(
            selected_index=int(self.options_list.current_index) + 1,
            number_of_documents=len(self.options_list.options),
        )

    def refresh(self, *args):
        self.refresh_status_line()

    def update(self, *args):
        self.options_list.update()
        self.refresh_status_line()

    def get_selection(self):
        return self.options_list.get_selection()

    def update_info_window(self):
        doc = self.options_list.get_selection()
        self.info_window.set_text(doc.dump())
