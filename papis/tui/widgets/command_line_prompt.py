from prompt_toolkit.filters import has_focus, Condition
from prompt_toolkit.layout.processors import BeforeInput
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.completion import WordCompleter, Completer, Completion
from prompt_toolkit.layout.containers import (
    HSplit, Window, WindowAlign, ConditionalContainer
)
from prompt_toolkit.layout.controls import (
    BufferControl,
    FormattedTextControl
)
from prompt_toolkit.application.current import get_app
from prompt_toolkit.utils import Event
import shlex


class Command(Event):
    """
    :param name: Name of the command
    :type  name: parameter_type
    :param run: A callable object where the first argument is the cmd itself.
    :type  run: callable
    """
    def __init__(self, name, run, aliases=[]):
        assert(isinstance(name, str)), 'name should be a string'
        assert(callable(run)), 'run should be callable'
        assert(isinstance(aliases, list))
        self.name = name
        self.run = run
        self.aliases = aliases

    @property
    def app(self):
        return get_app()

    @property
    def names(self):
        return [self.name] + self.aliases

    def __call__(self, *args, **kwargs):
        return self.run(self, *args, **kwargs)


class CommandLinePrompt(ConditionalContainer):
    """
    A vim-like command line prompt widget.
    It's supposed to be instantiated only once.
    """
    def __init__(self, commands=[]):
        assert(isinstance(commands, list))
        for c in commands:
            assert(isinstance(c, Command))
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

    def trigger(self):
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
        return cmds[0](*input_cmd)

    def clear(self):
        self.text = ''

    @property
    def text(self):
        return self.buf.text

    @text.setter
    def text(self, text):
        self.buf.text = text

