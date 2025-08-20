import pytest


def test_simple_command() -> None:
    from papis.tui.picker.widgets import Command

    cmd = Command("test", lambda c: 1 + 1)
    assert cmd.app is not None

    r = cmd.run(cmd)
    assert r == 2
    assert cmd.names == ["test"]

    cmd = Command("test", lambda c: 1 + 1, aliases=["t", "e"])
    assert cmd.names == ["test", "t", "e"]


def test_command_line_prompt() -> None:
    from papis.tui.picker.widgets import Command, CommandLinePrompt
    cmds = [Command("test", lambda c: 1 + 1)]
    prompt = CommandLinePrompt(commands=cmds)

    prompt.text = "test"
    prompt.trigger()

    prompt.text = "est"
    with pytest.raises(Exception,
                       match=r"No command found for 'est'"):
        prompt.trigger()

    prompt.text = ""
    prompt.trigger()

    prompt.commands = 2 * [Command("test", lambda c: 1 + 1)]
    prompt.text = "sdf asldfj dsafds"
    prompt.clear()
    assert prompt.text == ""

    prompt.text = "test"
    with pytest.raises(Exception,
                       match="More than one command matches the input"):
        prompt.trigger()
