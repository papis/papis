import sys
from collections.abc import Callable, Sequence
from typing import TypeVar

import papis.logging
import papis.pick
import papis.tui.app as tui

logger = papis.logging.get_logger(__name__)
T = TypeVar("T")


class Picker(papis.pick.Picker[T]):
    def __call__(
            self,
            options: Sequence[T],
            header_filter: Callable[[T], str] = str,
            match_filter: Callable[[T], str] = str,
            default_index: int = 0
            ) -> list[T]:

        if len(options) == 0:
            return []

        if len(options) == 1:
            return [options[0]]

        def run() -> list[T]:
            picker = tui.Picker(
                options,
                default_index,
                header_filter,
                match_filter
            )
            picker.run()

            return picker.options_list.get_selection()

        # NOTE: prompt_toolkit works in interactive mode, so when we call it
        # from something that is not a full terminal (e.g. in a pipe, redirect,
        # variable assignment a=$(papis ...)), it will hang waiting for input.
        #
        # This works around that by setting stdout to stderr when not isatty so
        # that prompt_toolkit writes to stderr and we can capture stdout and pipe it.
        #
        # WARN: This still won't work when stderr is redirected as well, e.g.
        #   papis list --id <QUERY> > stdout.txt 2> stderr.txt
        # so we just error out in that case.
        if not sys.stdout.isatty():
            if not sys.stderr.isatty():
                logger.error("Cannot show the picker when no interactive output "
                             "is available. Both 'stdout' and 'stderr' are not "
                             "connected as TTY interfaces (likely being piped to "
                             "some other process).")
                return []

            from contextlib import redirect_stdout

            with redirect_stdout(sys.stderr):
                return run()
        else:
            return run()
