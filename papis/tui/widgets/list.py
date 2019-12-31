import re
from prompt_toolkit.formatted_text.html import HTML
from prompt_toolkit.layout.screen import Point
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.containers import (
    Window, ConditionalContainer, WindowAlign, ScrollOffsets
)
from prompt_toolkit.filters import has_focus
import multiprocessing

import logging

logger = logging.getLogger('tui:widget:list')


def match_against_regex(regex, line, index):
    return index if regex.match(line) else None


class OptionsList(ConditionalContainer):

    def __init__(
            self,
            options,
            default_index=0,
            header_filter=lambda x: x,
            match_filter=lambda x: x,
            custom_filter=None,
            search_buffer=Buffer(multiline=False),
            cpu_count=multiprocessing.cpu_count()
            ):

        assert(isinstance(options, list))
        assert(callable(header_filter))
        assert(callable(match_filter))
        assert(isinstance(default_index, int))

        self.search_buffer = search_buffer
        self.last_query_text = ''
        self.search_buffer.on_text_changed += self.update

        self.header_filter = header_filter
        self.match_filter = match_filter
        self.current_index = default_index
        self.entries_left_offset = 0
        self.cpu_count = cpu_count

        self.options_headers_linecount = []
        self._indices_to_lines = []

        self._options = []
        self.marks = []
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
            # right_margins=[NumberedMargin()],
            # left_margins=[NumberedMargin()],
            align=WindowAlign.LEFT,
            height=None,
            get_line_prefix=self.get_line_prefix
            # get_line_prefix=lambda line, b: [('bg:red', '  ')]
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

    def get_line_prefix(self, line, blih):
        if self.current_index is None:
            return
        current_line = self.index_to_line(self.current_index)
        if (0 <= line - current_line
                < self.options_headers_linecount[self.current_index]):
            return [('class:options_list.selected_margin', '|')]
        else:
            marked_clines = [self.index_to_line(i) for i in self.marks]
            if line in marked_clines:
                return [('class:options_list.marked_margin', '#')]
            else:
                return [('class:options_list.unselected_margin', ' ')]

    def toggle_mark_current_selection(self):
        if self.current_index in self.marks:
            self.marks.pop(self.marks.index(self.current_index))
        else:
            self.mark_current_selection()

    def mark_current_selection(self):
        self.marks.append(self.current_index)

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

    def deselect(self):
        self.current_index = None

    def go_bottom(self):
        if len(self.indices) > 0:
            self.current_index = self.indices[-1]

    @property
    def query_text(self):
        return self.search_buffer.text

    @property
    def search_regex(self):
        cleaned_search = (
            self.query_text
            .replace('(', '\\(')
            .replace(')', '\\)')
            .replace('+', '\\+')
            .replace('[', '\\[')
            .replace(']', '\\]')
        )
        return re.compile(r".*"+re.sub(r"\s+", ".*", cleaned_search), re.I)

    def update(self, *args):
        self.filter_options()
        self._indices_to_lines = []

    def filter_options(self, *args):
        indices = []
        regex = self.search_regex

        if self.query_text == self.last_query_text:
            return

        if self.query_text.startswith(self.last_query_text):
            search_indices = self.indices
        else:
            search_indices = range(len(self.options_matchers))

        self.last_query_text = self.query_text

        with multiprocessing.Pool(self.cpu_count) as pool:
            results = [
                pool.apply_async(
                    match_against_regex,
                    args=(regex, opt, i,)
                )
                for i, opt in enumerate(self.options_matchers)
                if i in search_indices
            ]

            self.indices = [d.get() for d in results
                            if d.get(timeout=1) is not None]

        if len(self.indices) and self.current_index not in self.indices:
            if self.current_index > max(self.indices):
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
        except Exception:
            self.cursor = Point(0, 0)

    def get_tokens(self):
        self.update_cursor()
        result = sum(
            [self.options_headers[i] for i in self.indices],
            []
        )
        return result

    def index_to_line(self, index):
        if not self._indices_to_lines:
            options_headers_linecount = [
                self.options_headers_linecount[i] if i in self.indices else 0
                for i in range(len(self.options_headers_linecount))
            ]
            self._indices_to_lines = [
                sum(options_headers_linecount[0:i])
                for i in range(len(options_headers_linecount))
            ]
        return self._indices_to_lines[index]

    def process_options(self):
        logger.debug('processing {0} options'.format(len(self.options)))
        self.marks = []
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
            except Exception as e:
                logger.error(
                    'Error processing html for \n {0} \n {1}'.format(
                        prestring, e
                    )
                )
                htmlobject = [('fg:red', prestring)]
            self.options_headers += [htmlobject]
        logger.debug('got {0} headers'.format(len(self.options_headers)))
        logger.debug('processing matchers')
        self.options_matchers = [self.match_filter(o) for o in self.options]
        self.indices = range(len(self.options))
        logger.debug('got {0} matchers'.format(len(self.options_matchers)))
