import os
import sys
import pytest

from papis.testing import TemporaryLibrary, PapisRunner


def get_mock_script(name: str) -> str:
    """Constructs a command call for a command mocked by ``scripts.py``.

    :param name: the name of the command, e.g. ``ls`` or ``echo``.
    :returns: a string of the command
    """
    import sys

    script = os.path.join(os.path.dirname(__file__), "scripts.py")

    from papis.config import escape_interp

    return escape_interp(f"{sys.executable} {script} {name}")


@pytest.mark.library_setup(settings={
    "file-browser": get_mock_script("echo")
    })
def test_open_cli(tmp_library: TemporaryLibrary) -> None:
    from papis.commands.open import cli
    cli_runner = PapisRunner()

    result = cli_runner.invoke(
        cli,
        ["doc without files"])
    assert result.exit_code == 0

    result = cli_runner.invoke(
        cli,
        ["--tool", "nonexistingcommand", "Krishnamurti"],
        catch_exceptions=True)
    assert result.exit_code != 0
    assert result.exc_info[0] is FileNotFoundError

    result = cli_runner.invoke(
        cli,
        ["--tool", "nonexistingcommand", "--dir", "Krishnamurti"],
        catch_exceptions=True)
    assert result.exit_code == 0

    # Use a mock scriptlet
    result = cli_runner.invoke(
        cli,
        ["--tool", get_mock_script("echo"),
         "--mark", "--all", "Krishnamurti"])
    assert result.exit_code == 0


@pytest.mark.skipif(sys.platform != "win32", reason="uses windows commands")
def test_open_windows_cli(tmp_library: TemporaryLibrary) -> None:
    from papis.commands.open import cli
    cli_runner = PapisRunner()

    result = cli_runner.invoke(
        cli,
        ["--tool", "cmd.exe /c type", "--all", "Krishnamurti"])
    assert result.exit_code == 0
