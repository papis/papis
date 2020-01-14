import sys
from typing import Callable, Sequence, TypeVar

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
            ) -> Sequence[T]:

        if len(options) == 0:
            return []
        if len(options) == 1:
            return [options[0]]

        # patch stdout to stderr if the output is not a tty (terminal)
        oldstdout = sys.stdout
        if not sys.stdout.isatty():
            sys.stdout = sys.stderr
            sys.__stdout__ = sys.stderr

        picker = tui.Picker(
            options,
            default_index,
            header_filter,
            match_filter
        )
        picker.run()
        result = picker.options_list.get_selection()

        # restore the stdout to normality
        sys.stdout = oldstdout
        sys.__stdout__ = oldstdout

        return result
