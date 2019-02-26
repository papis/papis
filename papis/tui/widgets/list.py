import re
from prompt_toolkit.application.current import get_app
from prompt_toolkit.formatted_text.html import HTML, html_escape
from prompt_toolkit.filters import Condition
from prompt_toolkit.layout.screen import Point
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout.controls import (
    FormattedTextControl, BufferControl
)
from prompt_toolkit.widgets import HorizontalLine
from prompt_toolkit.layout.containers import (
    HSplit, Window, ConditionalContainer, WindowAlign, ScrollOffsets
)
from prompt_toolkit.filters import has_focus
from prompt_toolkit.layout import NumberedMargin
import multiprocessing

import logging

logger = logging.getLogger('tui:widget:list')


class OptionsList(ConditionalContainer):

    def __init__(
            self,
            options,
            default_index=0,
            header_filter=lambda x: x,
            match_filter=lambda x: x,
            custom_filter=None,
            search_buffer=Buffer(multiline=False)
            ):

        assert(isinstance(options, list))
        assert(callable(header_filter))
        assert(callable(match_filter))
        assert(isinstance(default_index, int))

        self.search_buffer = search_buffer
        self.search_buffer.on_text_changed += self.update

        self.header_filter = header_filter
        self.match_filter = match_filter
        self.current_index = default_index
        self.entries_left_offset = 0
        self.pool = multiprocessing.Pool(multiprocessing.cpu_count())

        self._options = []
        self.max_entry_height = 1
        # Options are processed here also through the setter
        self.options = options
        self.cursor = Point(0, 0)

        self.content = FormattedTextControl(
            text=self.get_tokens,
            focusable=False,
            key_bindings=None,
            get_cursor_position=lambda: self.cursor,
        )
        self.content_window = Window(
            content=self.content,
            wrap_lines=False,
            allow_scroll_beyond_bottom=True,
            scroll_offsets=ScrollOffsets(bottom=self.max_entry_height),
            cursorline=False,
            cursorcolumn=False,
            #right_margins=[NumberedMargin()],
            #left_margins=[NumberedMargin()],
            align=WindowAlign.LEFT,
            height=None,
            get_line_prefix=self.get_line_prefix
            #get_line_prefix=lambda line, b: [('bg:red', '  ')]
        )

        self.update()

        super(OptionsList, self).__init__(
            content=self.content_window,
            filter=(
                custom_filter
                if custom_filter is not None
                else has_focus(self.search_buffer)
            )
        )

    def __del__(self):
        # Clean initialized pool upon deleting of the object
        self.pool.close()
        self.pool.join()

    def get_line_prefix(self, line, blih):
        try:
            index = self.indices.index(self.current_index)
            cline = sum(
                self.options_headers_linecount[i]
                for i in self.indices[0:index]
            )
            cline = sum(
                self.options_headers_linecount[i]
                for i in self.indices[0:index]
            )
            if line == cline:
                return [('class:options_list.selected_margin', '>')]
            else:
                return [('class:options_list.unselected_margin', ' ')]
        except:
            return

    @property
    def options(self):
        return self._options

    @options.setter
    def options(self, new_options):
        self._options = new_options
        self.process_options()

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

    @property
    def search_regex(self):
        cleaned_search = (
            self.search_buffer.text
            .replace('(', '\\(')
            .replace(')', '\\)')
            .replace('+', '\\+')
            .replace('[', '\\[')
            .replace(']', '\\]')
        )
        return re.compile(r".*"+re.sub(r"\s+", ".*", cleaned_search), re.I)

    @staticmethod
    def match_against_regex(regex, line, index):
        return index if regex.match(line, re.I) else None

    def update(self, *args):
        self.filter_options()

    def filter_options(self, *args):
        indices = []
        regex = self.search_regex

        result = [
            self.pool.apply_async(
                OptionsList.match_against_regex,
                args=(regex, opt, i,)
            ) for i, opt in enumerate(self.options_matchers)
        ]

        indices =  [d.get() for d in result if d.get() is not None]

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

    def update_cursor(self):
        """This function updates the cursor according to the current index
        in the list.
        """
        try:
            index = self.indices.index(self.current_index)
            line = sum(
                self.options_headers_linecount[i]
                for i in self.indices[0:index]
            )
            self.cursor = Point(0, line)
        except Exception as e:
            self.cursor = Point(0, 0)

    def get_tokens(self):
        self.update_cursor()
        result = sum(
            [self.options_headers[i] for i in self.indices],
            []
        )
        return result

    def process_options(self):
        logger.debug('processing {0} options'.format(len(self.options)))
        self.options_headers_linecount = [
            len(self.header_filter(o).split('\n'))
            for o in self.options
        ]
        self.max_entry_height = max(self.options_headers_linecount)
        logger.debug('processing headers')
        self.options_headers = []
        for o in self.options:
            prestring = self.header_filter(o) + '\n'
            try:
                htmlobject = HTML(prestring).formatted_text
            except:
                logger.error(
                    'Error processing html for \n {0}'.format(prestring)
                )
                htmlobject = [ ('fg:red', prestring) ]
            self.options_headers += [htmlobject]
        logger.debug('got {0} headers'.format(len(self.options_headers)))
        logger.debug('processing matchers')
        self.options_matchers = [self.match_filter(o) for o in self.options]
        self.indices = range(len(self.options))
        logger.debug('got {0} matchers'.format(len(self.options_matchers)))
