from papis.tui.widgets.command_line_prompt import Command, CommandLinePrompt


def test_simple_command():
    cmd = Command("test", lambda c: 1 + 1)
    assert cmd.app is not None
    r = cmd.run(cmd)
    assert r == 2
    assert cmd.names == ["test"]

    cmd = Command("test", lambda c: 1 + 1, aliases=["t", "e"])
    assert cmd.names == ["test", "t", "e"]


def test_commandlineprompt():
    cmds = [Command("test", lambda c: 1 + 1)]
    prompt = CommandLinePrompt(commands=cmds)
    prompt.text = "test"
    re = prompt.trigger()
    assert re is None
    try:
        prompt.text = "est"
        e = prompt.trigger()
    except Exception as e:
        assert str(e) == "No command found (est)"
    else:
        assert False        # noqa: B011

    prompt.text = ""
    assert prompt.trigger() is None

    prompt.commands = 2 * [Command("test", lambda c: 1 + 1)]

    prompt.text = "sdf asldfj dsafds"
    prompt.clear()
    assert prompt.text == ""

    prompt.text = "test"
    try:
        prompt.trigger()
    except Exception as e:  # noqa: F841
        assert str(e) == "More than one command matches the input"
    else:
        assert False        # noqa: B011
