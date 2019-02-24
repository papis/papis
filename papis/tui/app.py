import os
from prompt_toolkit.application import (
    Application
)
from prompt_toolkit.history import FileHistory
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

from .widgets import (
    InfoWindow, CommandWindow, HelpWindow, OptionsListControl
)

logger = logging.getLogger('pick')


def create_keybindings(picker):
    kb = KeyBindings()

    @kb.add('c-q')
    @kb.add('c-c')
    def exit_(event):
        picker.deselect()
        event.app.exit()

    @kb.add('c-n', filter=~InfoWindow.is_shown)
    @kb.add('down', filter=~InfoWindow.is_shown)
    def down_(event):
        picker.options_list.move_down()
        picker.refresh()

    @kb.add('c-n', filter=InfoWindow.is_shown)
    def down_info(event):
        down_(event)
        update_info_window()

    @kb.add('c-p', filter=~InfoWindow.is_shown)
    @kb.add('up', filter=~InfoWindow.is_shown)
    def up_(event):
        picker.options_list.move_up()
        picker.refresh()

    @kb.add('c-p', filter=InfoWindow.is_shown)
    def up_info(event):
        up_(event)
        update_info_window()

    @kb.add('end')
    def go_end_(event):
        picker.options_list.go_bottom()
        picker.refresh()

    @kb.add('c-g')
    @kb.add('home')
    def go_top_(event):
        picker.options_list.go_top()
        picker.refresh()

    @kb.add('c-y')
    @kb.add('c-up')
    @kb.add('s-up')
    def scroll_up_(event):
        picker.scroll_up()
        picker.refresh_prompt()

    @kb.add('c-e')
    @kb.add('c-down')
    @kb.add('s-down')
    def scroll_down_(event):
        picker.scroll_down()
        picker.refresh_prompt()

    @kb.add('f1')
    def _help(event):
        HelpWindow.shown ^= True
        OptionsListControl.shown ^= True

    @kb.add(':')
    def _command_window(event):
        picker.layout.focus(picker.command_window.window)

    def update_info_window():
        doc = picker.options_list.get_selection()
        picker.info_window.set_text(doc.dump())

    @kb.add('c-i')
    def _info(event):
        update_info_window()
        if picker.layout.has_focus(picker.info_window.window):
            InfoWindow.shown = False
            picker.layout.focus(picker.search_buffer)
        else:
            InfoWindow.shown = True
            picker.layout.focus(picker.info_window.window)

    @kb.add('enter', filter=~has_focus(CommandWindow.instance))
    def enter_(event):
        event.app.exit()

    @kb.add('enter', filter=has_focus(CommandWindow.instance))
    def _enter_(event):
        # command = picker.command_window.buf.text
        picker.layout.focus(picker.search_buffer)
        CommandWindow.focus ^= True

    return kb


def get_picker():
    return Picker._actual_picker


class Picker(object):
    """The :class:`Picker <Picker>` object

    :param options: a list of options to choose from
    :param title: (optional) a title above options list
    :param indicator: (optional) custom the selection indicator
    :param default_index: (optional) set this if the default
        selected option is not the first one
    """

    _actual_picker = None

    def __init__(
            self,
            options,
            title=None,
            indicator='*',
            default_index=0,
            header_filter=lambda x: x,
            match_filter=lambda x: x
            ):

        Picker._actual_picker = self

        self.title = title
        self.indicator = indicator
        self.search = ""

        search_buffer_history = FileHistory(
            os.path.join('.', 'search_history')
        )

        self.search_buffer = Buffer(
            history=search_buffer_history,
            enable_history_search=True,
            multiline=False
        )

        self.prompt_buffer = Buffer(multiline=False)

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
        self.command_window = CommandWindow()

        root_container = HSplit([
            Window(height=1, content=BufferControl(buffer=self.search_buffer)),
            HorizontalLine(),
            HSplit([
                ConditionalContainer(
                    content=self.content_window,
                    filter=OptionsListControl.is_shown
                ),
                self.info_window.window,
            ]),
            self.help_window.window,
            self.command_window.window,
            ConditionalContainer(
                content=Window(
                    height=1,
                    style='reverse',
                    content=BufferControl(buffer=self.prompt_buffer)
                ),
                filter=~has_focus(CommandWindow.instance)
            ),
        ])

        self.layout = Layout(root_container)

        self.application = self._create_application()
        self.update()

    def deselect(self):
        self.options_list.current_index = None

    def _create_application(self):
        return Application(
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
        self.prompt_buffer.text = text

    def run(self):
        if len(self.options_list.options) == 0:
            return ""
        if len(self.options_list.options) == 1:
            return self.options_list.options[0]
        return self.application.run()
