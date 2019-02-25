import os
from prompt_toolkit.application import (
    Application
)
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
from prompt_toolkit.widgets import (
    HorizontalLine
)
import papis.config
import logging

from .widgets.command_line_prompt import Command
from .widgets import (
    InfoWindow, CommandLinePrompt, HelpWindow, OptionsListControl,
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

    @kb.add('c-n', filter=has_focus(app.info_window))
    def down_info(event):
        down_(event)
        update_info_window()

    @kb.add('c-p', filter=~has_focus(app.info_window))
    @kb.add('up', filter=~has_focus(app.info_window))
    def up_(event):
        event.app.options_list.move_up()
        event.app.refresh()

    @kb.add('c-p', filter=has_focus(app.info_window))
    def up_info(event):
        up_(event)
        update_info_window()

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
        event.app.scroll_up()
        event.app.refresh_prompt()

    @kb.add('c-e')
    @kb.add('c-down')
    @kb.add('s-down')
    def scroll_down_(event):
        event.app.scroll_down()
        event.app.refresh_prompt()

    @kb.add('f1', filter=~has_focus(app.help_window))
    def _help(event):
        event.app.layout.focus(app.help_window.window)
        event.app.message_toolbar.text = 'Press q to quit'
        OptionsListControl.shown ^= True

    @kb.add('q', filter=has_focus(app.help_window))
    def _help(event):
        event.app.layout.focus(app.help_window.window)
        event.app.layout.focus(app.command_line_prompt.window)
        event.app.message_toolbar.text = None
        OptionsListControl.shown ^= True

    @kb.add(':')
    def _command_window(event):
        event.app.layout.focus(app.command_line_prompt.window)

    def update_info_window():
        doc = picker.options_list.get_selection()
        picker.info_window.set_text(doc.dump())

    # @kb.add('c-i', filter=has_focus(app.info_window))
    # def _info(event):
        # event.app.layout.focus(event.app.search_buffer)

    # @kb.add('c-i', filter=~has_focus(app.info_window))
    # def _info_no_focus(event):
        # update_info_window()
        # event.app.layout.focus(app.info_window)

    @kb.add('enter', filter=~has_focus(app.command_line_prompt))
    def enter_(event):
        event.app.exit()

    @kb.add('enter', filter=has_focus(app.command_line_prompt))
    def _enter_(event):
        try:
            event.app.command_line_prompt.trigger()
        except Exception as e:
            MessageToolbar.instance.text = str(e)
        event.app.command_line_prompt.clear()
        event.app.layout.focus(event.app.search_buffer)

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

    return [
        Command("open", run=_open, aliases=["op"]),
        Command("edit", run=_edit, aliases=["e"]),
        Command("exit", run=_quit, aliases=["quit", "q"]),
        Command("echo", run=_echo),
        Command("help", run=lambda c: _echo(c, "To Be Implemented")),
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

        self.search = ""

        self.search_buffer = Buffer(multiline=False)

        self.options_list = OptionsListControl(
            options,
            self.search_buffer,
            default_index,
            header_filter,
            match_filter
        )

        self.search_buffer.on_text_changed += self.update

        self.content_window = Window(
            content=self.options_list.content,
            height=None,
            wrap_lines=False,
            ignore_content_height=True,
            always_hide_cursor=True,
            allow_scroll_beyond_bottom=True,
        )

        self.info_window = InfoWindow()
        self.help_window = HelpWindow()
        self.command_line_prompt = CommandLinePrompt(commands=get_commands())
        self.message_toolbar = MessageToolbar(style="bg:#bbee88 fg:#000000")
        self.status_line = MessageToolbar(style="bg:#ffffff fg:#000000")

        _root_container = HSplit([
            Window(height=1, content=BufferControl(buffer=self.search_buffer)),
            HorizontalLine(),
            HSplit([
                ConditionalContainer(
                    content=self.content_window,
                    filter=OptionsListControl.is_shown
                ),
                self.info_window,
            ]),
            self.help_window,
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

    def refresh_prompt(self):
        self.prompt_echo(
            "{0}/{1}  F1:help".format(
                int(self.options_list.current_index) + 1,
                len(self.options_list.options),
            )
        )

    def scroll_down(self):
        lvl = self.last_visible_line
        ll = self.content_height
        if ll and lvl:
            if lvl + 1 < ll:
                new = lvl + 1
            else:
                new = lvl
            self.options_list.cursor = Point(0, new)

    def scroll_up(self):
        fvl = self.first_visible_line
        if fvl:
            if fvl >= 0:
                new = fvl - 1
            else:
                new = 0
            self.options_list.cursor = Point(0, new)

    # def scroll_up(self):
        # dp = self.displayed_lines
        # if len(dp):
            # self.options_list.cursor = Point(0, dp[0] - 1)

    def refresh(self, *args):
        self.options_list.refresh()
        self.refresh_prompt()

    def update(self, *args):
        self.options_list.update()
        self.refresh_prompt()

    @property
    def screen_height(self):
        return self.options_list.content.preferred_height(None, None, None)

    @property
    def displayed_lines(self):
        info = self.content_window.render_info
        if info:
            return info.displayed_lines

    @property
    def first_visible_line(self):
        info = self.content_window.render_info
        if info:
            return info.first_visible_line()

    @property
    def last_visible_line(self):
        info = self.content_window.render_info
        if info:
            return info.last_visible_line()

    @property
    def content_height(self):
        info = self.content_window.render_info
        if info:
            return info.content_height

    def prompt_echo(self, text):
        self.status_line.text = text

    def get_selection(self):
        return self.options_list.get_selection()
