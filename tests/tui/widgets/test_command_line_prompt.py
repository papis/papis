from prompt_toolkit.layout.containers import to_container
from papis.tui.widgets.command_line_prompt import *
from papis.tui.widgets import *


def test_simple_command():
    cmd = Command('test', lambda c: 1+1)
    assert(cmd.app is not None)
    r = cmd()
    assert(r == 2)


def test_commandlineprompt():
    prompt = CommandLinePrompt()
    cmds = [Command('test', lambda c: 1+1)]
    prompt.commands = cmds
    prompt.text = 'test'
    prompt.trigger()
    try:
        prompt.text = 'est'
        e = prompt.trigger()
    except Exception as e:
        assert(str(e) == 'No command found (est)')
    else:
        assert(False)
