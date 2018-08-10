import os
import re
from prompt_toolkit.formatted_text import HTML
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
        picker.options_list.refresh()

    @kb.add('c-p')
    @kb.add('up')
    def up_(event):
        picker.options_list.move_up()
        picker.options_list.refresh()

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
            get_cursor_position=self.index_to_point,
            show_cursor=True,
            text=''
        )

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
            return Point(0, line)
        except:
            return Point(0,0)

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
        self.options_headers_linecount = [
            len(self.header_filter(o).split('\n'))
            for o in self.options
        ]
        self.options_headers = [
            HTML(
                re.sub(
                    r'^', ' ' * self.entries_left_offset,
                    re.sub(
                        r'\n', '\n' + ' ' * self.entries_left_offset,
                        self.header_filter(o)
                    )
                ) + '\n'
            ).formatted_text for o in self.options
        ]
        self.options_matchers = [self.match_filter(o) for o in self.options]
        self.indices = range(len(self.options))


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

    def update(self, *args):
        self.options_list.update()
        self.prompt_echo(
            "{}/{}".format(
                int(self.options_list.current_index) + 1,
                len(self.options_list.options)
            )
        )

    @property
    def screen_height(self):
        return self.options_list.content.preferred_height(None, None, None)

    @property
    def displayed_lines(self):
        info = self.content_window.render_info
        if info:
            return info.displayed_lines

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
