import os
import re
import functools
from typing import (
    Optional, Any, List, Generic, Sequence,
    Callable, Tuple, Pattern, TypeVar, Union)

from prompt_toolkit.formatted_text import HTML, AnyFormattedText, FormattedText
from prompt_toolkit.data_structures import Point
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.containers import (
    Window, ConditionalContainer, WindowAlign, ScrollOffsets
)
from prompt_toolkit.filters import Filter, has_focus

import papis.utils
import papis.logging

logger = papis.logging.get_logger(__name__)

Option = TypeVar("Option")


def match_against_regex(
        regex: Pattern[str],
        pair: Tuple[int, str]) -> Optional[int]:
    """Return index if line matches regex

        pair[0] is the index of the element
        and pair[1] is the line to be matched
    """
    return pair[0] if regex.match(pair[1]) else None


class OptionsList(ConditionalContainer, Generic[Option]):
    """This is the main widget containing a list of items (options) to select from.
    """

    def __init__(
            self,
            options: Sequence[Option],
            default_index: int = 0,
            header_filter: Callable[[Option], str] = str,
            match_filter: Callable[[Option], str] = str,
            custom_filter: Optional[Union[Filter, Callable[[str], bool]]] = None,
            search_buffer: Optional[Buffer] = None,
            cpu_count: Optional[int] = None) -> None:
        if search_buffer is None:
            search_buffer = Buffer(multiline=False)

        if cpu_count is None:
            cpu_count = os.cpu_count()

        self.search_buffer = search_buffer
        self.last_query_text = ""
        self.search_buffer.on_text_changed += self.update

        self.header_filter = header_filter
        self.match_filter = match_filter
        self.current_index: Optional[int] = default_index
        self.entries_left_offset = 0
        self.cpu_count = cpu_count

        self.options_headers_linecount: List[int] = []
        self._indices_to_lines: List[int] = []

        self.options_headers: List[FormattedText] = []
        self.options_matchers: List[str] = []
        self.indices: List[int] = []
        self._options: List[Option] = []
        self.marks: List[int] = []
        self.max_entry_height = 1

        # options are processed here also through the setter
        # ##################################################
        self.set_options(options)
        self.cursor = Point(0, 0)
        # ##################################################

        content = FormattedTextControl(
            text=self.get_tokens,
            focusable=False,
            key_bindings=None,
            get_cursor_position=lambda: self.cursor,
        )
        self.content_window = Window(
            content=content,
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
            # get_line_prefix=lambda line, b: [('bg:ansired', '  ')]
        )

        self.update()

        super().__init__(
            content=self.content_window,
            filter=(
                custom_filter   # type: ignore[arg-type]
                if custom_filter is not None
                else has_focus(self.search_buffer)
            )
        )

    def get_line_prefix(
            self,
            line: int,
            blih: int) -> AnyFormattedText:
        if self.current_index is None:
            return None

        current_line = self.index_to_line(self.current_index)
        if (0 <= line - current_line
                < self.options_headers_linecount[self.current_index]):
            return [("class:options_list.selected_margin", "|")]
        else:
            marked_lines = []
            for index in self.marks:
                start_line = self.index_to_line(index)
                end_line = start_line + self.options_headers_linecount[index]
                marked_lines.extend(range(start_line, end_line))
            if line in marked_lines:
                return [("class:options_list.marked_margin", "#")]
            else:
                return [("class:options_list.unselected_margin", " ")]

    def toggle_mark_current_selection(self) -> None:
        if self.current_index in self.marks:
            self.marks.pop(self.marks.index(self.current_index))
        else:
            self.mark_current_selection()

    def mark_current_selection(self) -> None:
        if self.current_index is not None:
            self.marks.append(self.current_index)

    def get_options(self) -> List[Option]:
        """Get the original options
        """
        return self._options

    def set_options(self, new_options: Sequence[Option]) -> None:
        """Set the options and process them"""
        self._options = list(new_options)
        self.process_options()

    def move_up(self) -> None:
        """Move the cursor up whenever possible"""
        if self.current_index is None:
            return None

        from contextlib import suppress
        with suppress(ValueError):
            index = self.indices.index(self.current_index)
            index -= 1
            if index < 0:
                self.current_index = self.indices[-1]
            else:
                self.current_index = self.indices[index]

    def move_down(self) -> None:
        """Move the cursor down whenever possible"""
        if self.current_index is None:
            return None

        from contextlib import suppress
        with suppress(ValueError):
            index = self.indices.index(self.current_index)
            index += 1
            if index >= len(self.indices):
                self.current_index = self.indices[0]
            else:
                self.current_index = self.indices[index]

    def go_top(self) -> None:
        """Go to top whenever possible"""
        if self.indices:
            self.current_index = self.indices[0]

    def deselect(self) -> None:
        """Do not select any option"""
        self.current_index = None

    def go_bottom(self) -> None:
        """Go to bottom whenever possible"""
        if len(self.indices) > 0:
            self.current_index = self.indices[-1]

    @property
    def query_text(self) -> str:
        """Get the query text"""
        return str(self.search_buffer.text)

    @property
    def search_regex(self) -> Pattern[str]:
        """Get and form the regular expression out of the query text"""
        cleaned_search = (
            self.query_text
            .replace("(", "\\(")
            .replace(")", "\\)")
            .replace("+", "\\+")
            .replace("[", "\\[")
            .replace("]", "\\]")
        )
        return re.compile(r".*" + re.sub(r"\s+", ".*", cleaned_search), re.I)

    def update(self, *args: Any) -> None:
        """Update the state"""
        # The *args is important for the buffer
        self.filter_options()
        self._indices_to_lines = []

    def filter_options(self) -> None:
        """Filter the items using the regular expression from the query"""
        regex = self.search_regex

        if self.query_text == self.last_query_text:
            return

        if self.query_text.startswith(self.last_query_text):
            search_indices = self.indices
        else:
            search_indices = list(range(len(self.options_matchers)))

        self.last_query_text = self.query_text

        f = functools.partial(match_against_regex, regex)
        results = papis.utils.parmap(f,
                                     [(i, matcher)
                                      for i, matcher in
                                      enumerate(self.options_matchers)
                                      if i in search_indices])

        self.indices = [i for i in results if i is not None]

        if (self.indices
                and self.current_index is not None
                and self.current_index not in self.indices):
            if self.current_index > max(self.indices):
                self.current_index = max(self.indices)
            else:
                self.current_index = self.indices[0]

    def get_selection(self) -> List[Option]:
        """Get the selected item, if there is Any"""
        if len(self.marks):
            return [self.get_options()[m] for m in self.marks]
        if self.indices and self.current_index is not None:
            return [self.get_options()[self.current_index]]
        return []

    def update_cursor(self) -> None:
        """This function updates the cursor according to the current index
        in the list.
        """
        if self.current_index is None:
            return
        try:
            index = self.indices.index(self.current_index)
            line = sum(
                self.options_headers_linecount[i]
                for i in self.indices[0:index]
            )
            self.cursor = Point(0, line)
        except Exception:
            self.cursor = Point(0, 0)

    def get_tokens(self) -> List[Tuple[str, str]]:
        """Creates the body of the list, which is just a list of tuples,
        where the tuples follow the FormattedText structure.
        """
        import time
        import operator

        self.update_cursor()
        begin_t = time.time()
        internal_text: List[Tuple[str, str]] = functools.reduce(
            operator.add,
            [self.options_headers[i] for i in self.indices],
            [])
        logger.debug("Created items in %.1f ms.", 1000 * (time.time() - begin_t))
        return internal_text

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
        logger.debug("Processing %d options.", len(self.get_options()))
        self.marks = []

        def _get_linecount(_o: Option) -> int:
            return len(self.header_filter(_o).split("\n"))

        self.options_headers_linecount = list(map(_get_linecount,
                                                  self.get_options()))
        self.max_entry_height = max(self.options_headers_linecount)
        logger.debug("Processing headers.")

        self.options_headers = []
        for _opt in self.get_options():
            prestring = self.header_filter(_opt) + "\n"
            try:
                htmlobject = HTML(prestring).formatted_text
            except Exception as exc:
                logger.error(
                    "Error processing HTML for '%s'.", prestring, exc_info=exc)
                htmlobject = FormattedText([("fg:ansired", prestring)])

            self.options_headers.append(htmlobject)

        logger.debug("Got %d headers.", len(self.options_headers))
        logger.debug("Processing matchers.")

        self.options_matchers = list(
            map(self.match_filter, self.get_options()))
        self.indices = list(range(len(self.get_options())))

        logger.debug("Got %d matchers.", len(self.options_matchers))
