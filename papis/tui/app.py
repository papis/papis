import os
from prompt_toolkit.application import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.enums import EditingMode
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.screen import Point
from prompt_toolkit.filters import has_focus
from prompt_toolkit.layout.containers import (
    HSplit, Window, ConditionalContainer
)
from prompt_toolkit.layout.controls import (
    BufferControl,
)
from prompt_toolkit.layout.layout import Layout
import papis.config
import logging

from .widgets.command_line_prompt import Command
from .widgets import (
    InfoWindow, CommandLinePrompt, HelpWindow, OptionsList,
    MessageToolbar
)

logger = logging.getLogger('pick')


def create_keybindings(app):
    kb = KeyBindings()

    @kb.add('c-q')
    @kb.add('c-c')
    def exit_(event):
        event.app.deselect()
        event.app.exit()

    @kb.add('c-n', filter=~has_focus(app.info_window))
    @kb.add('down', filter=~has_focus(app.info_window))
    def down_(event):
        event.app.options_list.move_down()
        event.app.refresh()
        event.app.update()

    @kb.add('c-n', filter=has_focus(app.info_window))
    def down_info(event):
        down_(event)
        event.app.update_info_window()

    @kb.add('c-p', filter=~has_focus(app.info_window))
    @kb.add('up', filter=~has_focus(app.info_window))
    def up_(event):
        event.app.options_list.move_up()
        event.app.refresh()
        event.app.update()

    @kb.add('c-p', filter=has_focus(app.info_window))
    def up_info(event):
        up_(event)
        event.app.update_info_window()

    @kb.add('end')
    def go_end_(event):
        event.app.options_list.go_bottom()
        event.app.refresh()

    @kb.add('c-g')
    @kb.add('home')
    def go_top_(event):
        event.app.options_list.go_top()
        event.app.refresh()

    @kb.add('c-y')
    @kb.add('c-up')
    @kb.add('s-up')
    def scroll_up_(event):
        event.app.options_list.scroll_up()
        event.app.refresh_status_line()

    @kb.add('c-e')
    @kb.add('c-down')
    @kb.add('s-down')
    def scroll_down_(event):
        event.app.options_list.scroll_down()
        event.app.refresh_status_line()

    @kb.add('f1', filter=~has_focus(app.help_window))
    def _help(event):
        event.app.layout.focus(app.help_window.window)
        event.app.message_toolbar.text = 'Press q to quit'

    @kb.add('q', filter=has_focus(app.help_window))
    def _help(event):
        event.app.layout.focus(app.help_window.window)
        event.app.layout.focus(app.command_line_prompt.window)
        event.app.message_toolbar.text = None
        event.app.layout.focus(event.app.options_list.search_buffer)

    @kb.add(':')
    def _command_window(event):
        event.app.layout.focus(app.command_line_prompt.window)

    @kb.add('c-i', filter=has_focus(app.info_window))
    def _info(event):
        event.app.layout.focus(event.app.options_list.search_buffer)

    @kb.add('c-i', filter=~has_focus(app.info_window))
    def _info_no_focus(event):
        event.app.update_info_window()
        event.app.layout.focus(app.info_window.window)

    @kb.add('enter', filter=~has_focus(app.command_line_prompt))
    def enter_(event):
        event.app.exit()

    @kb.add('enter', filter=has_focus(app.command_line_prompt))
    def _enter_(event):
        try:
            event.app.command_line_prompt.trigger()
        except Exception as e:
            event.app.error_toolbar.text = str(e)
        event.app.command_line_prompt.clear()
        event.app.layout.focus(event.app.options_list.search_buffer)

    return kb


def get_commands():

    def _open(cmd):
        from papis.commands.open import run
        doc = cmd.app.get_selection()
        run(doc)

    def _edit(cmd):
        from papis.commands.edit import run
        doc = cmd.app.get_selection()
        run(doc)
        cmd.app.invalidate()

    def _quit(cmd):
        cmd.app.deselect()
        cmd.app.exit()

    def _echo(cmd, *args):
        cmd.app.message_toolbar.text = ' '.join(args)

    def _info(cmd):
        cmd.app.update_info_window()
        cmd.app.layout.focus(cmd.app.info_window.window)

    return [
        Command("open", run=_open, aliases=["op"]),
        Command("edit", run=_edit, aliases=["e"]),
        Command("exit", run=_quit, aliases=["quit", "q"]),
        Command("info", run=_info, aliases=["i"]),
        Command("echo", run=_echo),
        Command("help",
            run=lambda c: c.app.layout.focus(c.app.help_window.window)
        ),
    ]


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
        self.command_line_prompt = CommandLinePrompt(commands=get_commands())
        self.message_toolbar = MessageToolbar(style="bg:#bbee88 fg:#000000")
        self.error_toolbar = MessageToolbar(style="bg:#ff0022 fg:#000000")
        self.status_line = MessageToolbar(style="bg:#ffffff fg:#000000")

        self.options_list = OptionsList(
            options,
            default_index,
            header_filter,
            match_filter,
            custom_filter=~has_focus(self.help_window)
        )

        _root_container = HSplit([
            HSplit([
                self.options_list,
                self.info_window,
            ]),
            self.help_window,
            self.error_toolbar,
            self.message_toolbar,
            self.status_line,
            self.command_line_prompt.window,
        ])

        self.layout = Layout(_root_container)

        super(Picker, self).__init__(
            input=None,
            output=None,
            editing_mode=EditingMode.EMACS
            if papis.config.get('tui-editmode') == 'emacs'
            else EditingMode.VI,
            layout=self.layout,
            key_bindings=create_keybindings(self),
            include_default_pygments_style=False,
            full_screen=True,
            enable_page_navigation_bindings=True
        )
        self.update()

    def deselect(self):
        self.options_list.current_index = None

    def refresh_status_line(self):
        self.status_line.text = "{0}/{1}  F1:help".format(
            int(self.options_list.current_index) + 1,
            len(self.options_list.options),
        )

    def refresh(self, *args):
        self.options_list.refresh()
        self.refresh_status_line()

    def update(self, *args):
        self.options_list.update()
        self.refresh_status_line()

    def get_selection(self):
        return self.options_list.get_selection()

    def update_info_window(self):
        doc = self.options_list.get_selection()
        self.info_window.set_text(doc.dump())
