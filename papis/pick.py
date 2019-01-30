import os
import re
from prompt_toolkit.formatted_text.html import HTML, html_escape
from prompt_toolkit.application import (
    Application as PromptToolkitApplication,
)
from prompt_toolkit.history import FileHistory
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.enums import EditingMode
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.screen import Point
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.widgets import (
    HorizontalLine
)
import papis.config
import logging
logger = logging.getLogger('pick')

__all__ = ['Picker', 'pick']


def create_keybindings(picker):
    kb = KeyBindings()

    @kb.add('c-q')
    @kb.add('c-c')
    def exit_(event):
        picker.deselect()
        event.app.exit()

    @kb.add('c-n')
    @kb.add('down')
    def down_(event):
        picker.options_list.move_down()
        picker.refresh()

    @kb.add('c-p')
    @kb.add('up')
    def up_(event):
        picker.options_list.move_up()
        picker.refresh()

    @kb.add('end')
    def up_(event):
        picker.options_list.go_bottom()
        picker.refresh()

    @kb.add('c-g')
    @kb.add('home')
    def up_(event):
        picker.options_list.go_top()
        picker.refresh()

    @kb.add('c-y')
    @kb.add('c-up')
    @kb.add('s-up')
    def up_(event):
        picker.scroll_up()
        picker.refresh_prompt()

    @kb.add('c-e')
    @kb.add('c-down')
    @kb.add('s-down')
    def up_(event):
        picker.scroll_down()
        picker.refresh_prompt()

    @kb.add('f1')
    def help(event):
        picker.options_list.content.text = """
Bindings:

Ctrl-e, Ctrl-down, Shift-down : Scroll Down
Ctrl-y, Ctrl-up,   Shift-up   : Scroll up
Ctrl-n, down                  : Next item
Ctrl-p, up                    : Previous item
Ctrl-q, Ctrl-c                : Quit
Home                          : First item
End                           : Last item

"""
        picker.refresh_prompt()

    # @kb.add('/')
    # def up_(event):
        # picker.layout.focus(picker.search_buffer)

    # @kb.add('c-f')
    # def up_(event):
        # if picker.layout.has_focus(picker.content_window):
            # picker.layout.focus(picker.search_buffer)
        # else:
            # picker.layout.focus(picker.content_window)

    @kb.add('enter')
    def enter_(event):
        event.app.exit()

    return kb


class OptionsListControl:

    def __init__(
            self,
            options,
            search_buffer,
            default_index=0,
            header_filter=None,
            match_filter=None
            ):

        self.options = options
        self.search_buffer = search_buffer
        self.header_filter = header_filter
        self.match_filter = match_filter
        self.current_index = default_index
        self.entries_left_offset = 2

        self.process_options()

        self.content = FormattedTextControl(
            key_bindings=None,
            #get_cursor_position=self.index_to_point,
            get_cursor_position=lambda: self.cursor,
            show_cursor=True,
            text=''
        )
        self.cursor = Point(0,0)

    def set_options(self, options):
        self.options = options
        self.process_options()

    def index_to_point(self):
        try:
            index = self.indices.index(self.current_index)
            line = sum(
                self.options_headers_linecount[i]
                for i in self.indices[0:index]
            )
            self.cursor = Point(0, line)
        except Exception as e:
            self.cursor = Point(0,0)

    def move_up(self):
        try:
            index = self.indices.index(self.current_index)
            index -= 1
            if index < 0:
                self.current_index = self.indices[-1]
            else:
                self.current_index = self.indices[index]
        except ValueError:
            pass

    def move_down(self):
        try:
            index = self.indices.index(self.current_index)
            index += 1
            if index >= len(self.indices):
                self.current_index = self.indices[0]
            else:
                self.current_index = self.indices[index]
        except ValueError:
            pass

    def go_top(self):
        if len(self.indices) > 0:
            self.current_index = self.indices[0]

    def go_bottom(self):
        if len(self.indices) > 0:
            self.current_index = self.indices[-1]

    def get_search_regex(self):
        cleaned_search = self.search_buffer.text.replace('(', '\\(')\
                                       .replace(')', '\\)')\
                                       .replace('+', '\\+')\
                                       .replace('[', '\\[')\
                                       .replace(']', '\\]')
        return r".*"+re.sub(r"\s+", ".*", cleaned_search)

    def update(self, *args):
        self.filter_options()
        self.refresh()

    def filter_options(self, *args):
        indices = []
        regex = self.get_search_regex()
        for index, option in enumerate(list(self.options)):
            if re.match(regex, self.options_matchers[index], re.I):
                indices += [index]
        self.indices = indices
        if len(self.indices) and self.current_index not in self.indices:
            if self.current_index < min(self.indices):
                self.current_index = self.indices[0]
            elif self.current_index > max(self.indices):
                self.current_index = max(self.indices)
            else:
                self.current_index = self.indices[0]

    def get_selection(self):
        if len(self.indices) and self.current_index is not None:
            return self.options[self.current_index]

    def refresh(self):
        self.index_to_point()
        i = self.current_index
        oldtuple = self.options_headers[i][0]
        self.options_headers[i][0] = (
            oldtuple[0],
            '>' + re.sub(r'^ ', '', oldtuple[1]),
        )
        self.content.text = sum(
            [self.options_headers[i] for i in self.indices],
            []
        )
        self.options_headers[i][0] = oldtuple

    def process_options(self):
        logger.debug('processing options')
        self.options_headers_linecount = [
            len(self.header_filter(o).split('\n'))
            for o in self.options
        ]
        logger.debug('processing headers')
        self.options_headers = []
        for o in self.options:
            prestring = re.sub(
                r'^', ' ' * self.entries_left_offset,
                re.sub(
                    r'\n', '\n' + ' ' * self.entries_left_offset,
                    self.header_filter(o)
                )
            ) + '\n'
            try:
                htmlobject = HTML(prestring).formatted_text
            except:
                logger.error(
                    'Error processing html for \n {0}'.format(prestring)
                )
                htmlobject = HTML(html_escape(prestring)).formatted_text
            self.options_headers += [htmlobject]
        logger.debug('processing matchers')
        self.options_matchers = [self.match_filter(o) for o in self.options]
        self.indices = range(len(self.options))
        logger.debug('options processed')


class Picker(object):
    """The :class:`Picker <Picker>` object

    :param options: a list of options to choose from
    :param title: (optional) a title above options list
    :param indicator: (optional) custom the selection indicator
    :param default_index: (optional) set this if the default
        selected option is not the first one
    """

    def __init__(
            self,
            options,
            title=None,
            indicator='*',
            default_index=0,
            header_filter=lambda x: x,
            match_filter=lambda x: x
            ):

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
        root_container = HSplit([
            Window(height=1, content=BufferControl(buffer=self.search_buffer)),
            HorizontalLine(),
            self.content_window,
            Window(height=1, content=BufferControl(buffer=self.prompt_buffer)),
        ])

        self.layout = Layout(root_container)

        self.application = self._create_application()
        self.update()

    def deselect(self):
        self.options_list.current_index = None

    def _create_application(self):
        return PromptToolkitApplication(
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

        # self.prompt_echo(
            # "{0}/{1} ={2}-{3} +{4} -{5}  <{6},{7}>".format(
                # int(self.options_list.current_index) + 1,
                # len(self.options_list.options),
                # self.displayed_lines[0] if self.displayed_lines is not None \
                    # else '',
                # self.displayed_lines[-1] if self.displayed_lines is not None \
                    # else '',
                # self.options_list.cursor,
                # self.content_height,
                # self.first_visible_line,
                # self.last_visible_line,
            # )
        # )

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

    def scroll_up(self):
        dp = self.displayed_lines
        if len(dp):
            self.options_list.cursor = Point(0, dp[0] - 1)

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


def pick(
        options,
        title="Pick: ",
        indicator='>',
        default_index=0,
        header_filter=lambda x: x,
        match_filter=lambda x: x
        ):
    """Construct and start a :class:`Picker <Picker>`.
    """

    if len(options) == 0:
        return ""
    if len(options) == 1:
        return options[0]

    picker = Picker(
                options,
                title,
                indicator,
                default_index,
                header_filter,
                match_filter
                )
    picker.run()
    return picker.options_list.get_selection()
