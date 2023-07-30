import os
import pytest

from tests.testlib import TemporaryLibrary, PapisRunner

script = os.path.join(os.path.dirname(__file__), "scripts.py")


@pytest.mark.library_setup(settings={
    "file-browser": "echo"
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
    assert result.exc_info[0] == FileNotFoundError

    result = cli_runner.invoke(
        cli,
        ["--tool", "nonexistingcommand", "--dir", "Krishnamurti"],
        catch_exceptions=True)
    assert result.exit_code == 0

    result = cli_runner.invoke(
        cli,
        ["--tool", "python {} echo".format(script), "--mark", "--all", "Krishnamurti"])
    assert result.exit_code == 0
