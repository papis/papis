import re
from prompt_toolkit.formatted_text.html import HTML
from prompt_toolkit.formatted_text.base import FormattedText
from prompt_toolkit.layout.screen import Point
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.containers import (
    Window, ConditionalContainer, WindowAlign, ScrollOffsets
)
from prompt_toolkit.filters import has_focus
import multiprocessing
import operator

import logging
from typing import (
    Optional, Dict, Any, List, Union, Generic,
    Callable, Tuple, Pattern, Sequence, TypeVar)

Option = TypeVar("Option")

logger = logging.getLogger('tui:widget:list')


def match_against_regex(
        regex: Pattern[str],
        line: str,
        index: int) -> Optional[int]:
    return index if regex.match(line) else None


class OptionsList(ConditionalContainer, Generic[Option]):  # type: ignore

    def __init__(
            self,
            options: List[Option],
            default_index: int = 0,
            header_filter: Callable[[Option], str] = lambda x: str(x),
            match_filter: Callable[[Option], str] = lambda x: str(x),
            custom_filter: Optional[Callable[[str], bool]] = None,
            search_buffer: Buffer = Buffer(multiline=False),
            cpu_count: int = multiprocessing.cpu_count()
            ):

        self.search_buffer = search_buffer
        self.last_query_text = ''  # type: str
        self.search_buffer.on_text_changed += self.update

        self.header_filter = header_filter
        self.match_filter = match_filter
        self.current_index = default_index  # type: Optional[int]
        self.entries_left_offset = 0
        self.cpu_count = cpu_count

        self.options_headers_linecount = []  # type: List[int]
        self._indices_to_lines = []  # type: List[int]

        self.options_headers = []  # type: FormattedText
        self.options_matchers = []  # type: List[str]
        self.indices = []  # type: List[int]
        self._options = []  # type: List[Option]
        self.marks = []  # type: List[int]
        self.max_entry_height = 1  # type: int
        # Options are processed here also through the setter
        self.set_options(options)  # type: List[Option]
        self.cursor = Point(0, 0)  # type: Point

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

    def get_line_prefix(self,
            line: int, blih: Any) -> Optional[List[Tuple[str, str]]]:
        if self.current_index is None:
            return None
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

    def toggle_mark_current_selection(self) -> None:
        if self.current_index in self.marks:
            self.marks.pop(self.marks.index(self.current_index))
        else:
            self.mark_current_selection()

    def mark_current_selection(self) -> None:
        if self.current_index:
            self.marks.append(self.current_index)

    def get_options(self) -> List[Option]:
        return self._options

    def set_options(self, new_options: List[Option]) -> None:
        self._options = new_options
        self.process_options()

    def move_up(self) -> None:
        if not self.current_index:
            return None
        try:
            index = self.indices.index(self.current_index)
            index -= 1
            if index < 0:
                self.current_index = self.indices[-1]
            else:
                self.current_index = self.indices[index]
        except ValueError:
            pass

    def move_down(self) -> None:
        if not self.current_index:
            return None
        try:
            index = self.indices.index(self.current_index)
            index += 1
            if index >= len(self.indices):
                self.current_index = self.indices[0]
            else:
                self.current_index = self.indices[index]
        except ValueError:
            pass

    def go_top(self) -> None:
        if len(self.indices) > 0:
            self.current_index = self.indices[0]

    def deselect(self) -> None:
        self.current_index = None

    def go_bottom(self) -> None:
        if len(self.indices) > 0:
            self.current_index = self.indices[-1]

    @property
    def query_text(self) -> str:
        return str(self.search_buffer.text)

    @property
    def search_regex(self) -> Pattern[str]:
        cleaned_search = (
            self.query_text
            .replace('(', '\\(')
            .replace(')', '\\)')
            .replace('+', '\\+')
            .replace('[', '\\[')
            .replace(']', '\\]')
        )
        return re.compile(r".*"+re.sub(r"\s+", ".*", cleaned_search), re.I)

    def update(self, *args: Any) -> None:
        self.filter_options()
        self._indices_to_lines = []

    def filter_options(self, *args: Any) -> None:
        indices = []  # type: List[int]
        regex = self.search_regex

        if self.query_text == self.last_query_text:
            return

        if self.query_text.startswith(self.last_query_text):
            search_indices = self.indices
        else:
            search_indices = list(range(len(self.options_matchers)))

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

            _maybe_indices = [d.get() for d in results]
            self.indices = [i for i in _maybe_indices if i is not None]

        if (len(self.indices)
             and self.current_index is not None
             and self.current_index not in self.indices):
            if self.current_index > max(self.indices):
                self.current_index = max(self.indices)
            else:
                self.current_index = self.indices[0]

    def get_selection(self) -> Optional[Option]:
        if len(self.indices) and self.current_index is not None:
            return self.get_options()[self.current_index]
        else:
            return None

    def update_cursor(self) -> None:
        """This function updates the cursor according to the current index
        in the list.
        """
        if not self.current_index:
            return None
        try:
            index = self.indices.index(self.current_index)
            line = sum(
                self.options_headers_linecount[i]
                for i in self.indices[0:index]
            )
            self.cursor = Point(0, line)
        except Exception:
            self.cursor = Point(0, 0)

    def get_tokens(self) -> List[FormattedText]:
        self.update_cursor()
        return list(operator.itemgetter(*self.indices)(self.options_headers))

    def index_to_line(self, index: int) -> int:
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

    def process_options(self) -> None:
        logger.debug('processing {0} options'.format(len(self.get_options())))
        self.marks = []
        def _get_linecount(o: Option) -> int:
            return len(self.header_filter(o).split('\n'))
        self.options_headers_linecount = list(map(_get_linecount,
                                                  self.get_options()))
        self.max_entry_height = max(self.options_headers_linecount)
        logger.debug('processing headers')
        self.options_headers = []
        for o in self.get_options():
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
        self.options_matchers = list(map(self.match_filter, self.get_options()))
        self.indices = list(range(len(self.get_options())))
        logger.debug('got {0} matchers'.format(len(self.options_matchers)))
