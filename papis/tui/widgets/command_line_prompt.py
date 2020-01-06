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
import shlex
from typing import Any, List, Callable


class Command:
    """
    :param name: Name of the command
    :type  name: parameter_type
    :param run: A callable object where the first argument is the cmd itself.
    :type  run: callable
    """
    def __init__(
            self,
            name: str,
            run: Callable[['Command'], Any],
            aliases: List[str] = []):
        self.name = name
        self.run = run
        self.aliases = aliases

    @property
    def app(self) -> Application:
        return get_app()

    @property
    def names(self) -> List[str]:
        return [self.name] + self.aliases


class CommandLinePrompt(ConditionalContainer):  # type: ignore
    """
    A vim-like command line prompt widget.
    It's supposed to be instantiated only once.
    """
    def __init__(self, commands: List[Command] = []):
        self.commands = commands
        wc = WordCompleter(sum([c.names for c in commands], []))
        self.buf = Buffer(
            completer=wc, complete_while_typing=True
        )
        self.buf.text = ''
        self.window = Window(
            content=BufferControl(
                buffer=self.buf,
                input_processors=[BeforeInput(':')]
            ),
            height=1
        )
        super(CommandLinePrompt, self).__init__(
            content=self.window,
            filter=has_focus(self.window)
        )

    def trigger(self) -> None:
        input_cmd = shlex.split(self.buf.text)
        if not input_cmd:
            return
        name = input_cmd[0]
        cmds = list(filter(lambda c: name in c.names, self.commands))

        if len(cmds) > 1:
            raise Exception('More than one command matches the input')
        elif len(cmds) == 0:
            raise Exception('No command found ({0})'.format(name))

        input_cmd.pop(0)
        cmds[0].run(cmds[0], *input_cmd)

    def clear(self) -> None:
        self.text = ''

    @property
    def text(self) -> Any:
        return self.buf.text

    @text.setter
    def text(self, text: str) -> None:
        self.buf.text = text
