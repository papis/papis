from typing import Any, List, Callable, Optional

from prompt_toolkit.application import Application
from prompt_toolkit.layout.processors import BeforeInput
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.layout.containers import (
    Window, ConditionalContainer
)
from prompt_toolkit.layout.controls import (
    BufferControl,
)
from prompt_toolkit.application.current import get_app
from prompt_toolkit.filters import has_focus


class Command:
    """
    .. attribute:: name

        Name of the command

    .. attribute:: run

        A callable object where the first argument is the cmd itself.

    .. attribute:: aliases

        A list of aliases for the command.

    .. attribute:: app
    .. attribute:: names
    """
    def __init__(
            self,
            name: str,
            run: Callable[["Command"], Any],
            aliases: Optional[List[str]] = None) -> None:
        if aliases is None:
            aliases = []

        self.name = name
        self.run = run
        self.aliases = aliases

    @property
    def app(self) -> Application[Any]:
        return get_app()

    @property
    def names(self) -> List[str]:
        return [self.name, *self.aliases]


class CommandLinePrompt(ConditionalContainer):
    """
    A vim-like command line prompt widget.
    It's supposed to be instantiated only once.
    """
    def __init__(self, commands: Optional[List[Command]] = None) -> None:
        if commands is None:
            commands = []

        from itertools import chain

        self.commands = commands
        names: List[str] = list(chain.from_iterable(c.names for c in commands))
        wc = WordCompleter(names)
        self.buf = Buffer(
            completer=wc, complete_while_typing=True
        )
        self.buf.text = ""
        self.window = Window(
            content=BufferControl(
                buffer=self.buf,
                input_processors=[BeforeInput(":")]
            ),
            height=1
        )
        super().__init__(
            content=self.window,
            filter=has_focus(self.window)
        )

    def trigger(self) -> None:
        import shlex
        input_cmd = shlex.split(self.buf.text)
        if not input_cmd:
            return
        name = input_cmd[0]
        cmds = list(filter(lambda c: name in c.names, self.commands))

        if len(cmds) > 1:
            raise ValueError(
                "More than one command matches the input: ['{}']"
                .format("', '".join(cmd.name for cmd in cmds)))
        elif not cmds:
            raise ValueError(f"No command found for '{name}'")

        input_cmd.pop(0)
        cmds[0].run(cmds[0], *input_cmd)

    def clear(self) -> None:
        self.text = ""

    @property
    def text(self) -> Any:
        return self.buf.text

    @text.setter
    def text(self, text: str) -> None:
        self.buf.text = text
