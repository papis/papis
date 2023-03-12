import os

import papis.config

from tests.testlib import TemporaryLibrary, PapisRunner


def test_git_cli(tmp_library: TemporaryLibrary) -> None:
    from papis.commands.git import cli
    cli_runner = PapisRunner()

    result = cli_runner.invoke(
        cli,
        ["init"])
    assert result.exit_code == 0

    folder, = papis.config.get_lib_dirs()
    assert os.path.exists(os.path.join(folder, ".git"))
