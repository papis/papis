import re
from prompt_toolkit.formatted_text.html import HTML, html_escape
from prompt_toolkit.filters import Condition
from prompt_toolkit.layout.containers import ConditionalContainer
from prompt_toolkit.layout.screen import Point
from prompt_toolkit.layout.controls import (
    FormattedTextControl
)

import logging

logger = logging.getLogger('tui:widget:list')


class OptionsListControl:

    shown = True

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
            # get_cursor_position=self.index_to_point,
            get_cursor_position=lambda: self.cursor,
            show_cursor=True,
            text=''
        )
        self.cursor = Point(0, 0)

    @Condition
    def is_shown():
        return OptionsListControl.shown

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
            self.cursor = Point(0, 0)

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
        cleaned_search = (
            self.search_buffer.text
            .replace('(', '\\(')
            .replace(')', '\\)')
            .replace('+', '\\+')
            .replace('[', '\\[')
            .replace(']', '\\]')
        )
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
