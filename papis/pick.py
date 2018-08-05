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

    # @kb.add('c-x', 'c-h')
    # def _(event):
        # picker.content.text = 'help \n' * 10

    # @kb.add('c-x', 'c-o')
    # def open(event):
        # import papis.commands.open
        # doc = picker.get_selection()
        # papis.commands.open.run(doc)

    # @kb.add('c-x', 'c-e')
    # def edit(event):
        # import papis.commands.edit
        # doc = picker.get_selection()
        # papis.commands.edit.run(doc)

    @kb.add('c-n')
    @kb.add('down')
    def down_(event):
        picker.move_down()
        picker.update()

    @kb.add('c-p')
    @kb.add('up')
    def up_(event):
        picker.move_up()
        picker.update()

    @kb.add('enter')
    def enter_(event):
        event.app.exit()

    return kb


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
            body_filter=None,
            match_filter=lambda x: x
            ):

        self.options = options
        self.title = title
        self.indicator = indicator
        self.search = ""
        self.header_filter = header_filter
        self.body_filter = body_filter
        self.match_filter = match_filter

        self.entries_left_offset = 2

        self.process_options()

        self.current_index = default_index

        search_buffer_history = FileHistory(
            os.path.join('.', 'search_history')
        )
        self.search_buffer = Buffer(
            history=search_buffer_history,
            enable_history_search=True,
            multiline=False
        )

        self.prompt_buffer = Buffer(multiline=False)

        self.search_buffer.on_text_changed += self.update

        self.content = FormattedTextControl(text='')
        self.content_window = Window(
            content=self.content,
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

    def process_options(self):
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

    def get_search_regex(self):
        cleaned_search = self.search_buffer.text.replace('(', '\\(')\
                                       .replace(')', '\\)')\
                                       .replace('+', '\\+')\
                                       .replace('[', '\\[')\
                                       .replace(']', '\\]')
        return r".*"+re.sub(r"\s+", ".*", cleaned_search)

    def deselect(self):
        self.current_index = None

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

    @property
    def screen_height(self):
        return self.content.preferred_height(None, None, None)

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

    def prompt_echo(self, text):
        self.prompt_buffer.text = text

    def update(self, *args):
        self.filter_options()
        self.refresh()
        self.prompt_echo(
            "{}/{}".format(int(self.current_index) + 1, len(self.options))
        )

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

    def run(self):
        if len(self.options) == 0:
            return ""
        if len(self.options) == 1:
            return self.options[0]
        return self.application.run()


def pick(
        options,
        title="Pick: ",
        indicator='>',
        default_index=0,
        header_filter=lambda x: x,
        body_filter=None,
        match_filter=lambda x: x
        ):
    """Construct and start a :class:`Picker <Picker>`.
    """
    picker = Picker(
                options,
                title,
                indicator,
                default_index,
                header_filter,
                body_filter,
                match_filter
                )
    picker.run()
    return picker.get_selection()
