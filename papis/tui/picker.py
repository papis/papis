import sys
from typing import Callable, List, Sequence, TypeVar

import papis.pick
import papis.tui.app as tui

T = TypeVar("T")


class Picker(papis.pick.Picker[T]):
    def __call__(
            self,
            options: Sequence[T],
            header_filter: Callable[[T], str] = str,
            match_filter: Callable[[T], str] = str,
            default_index: int = 0
            ) -> List[T]:

        if len(options) == 0:
            return []

        if len(options) == 1:
            return [options[0]]

        picker = tui.Picker(
            options,
            default_index,
            header_filter,
            match_filter
        )

        from contextlib import redirect_stdout

        if not sys.stdout.isatty():
            with redirect_stdout(sys.stderr):
                picker.run()
        else:
            picker.run()

        return picker.options_list.get_selection()
