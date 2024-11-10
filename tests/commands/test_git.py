import os
import shutil

import pytest

import papis.config

from papis.testing import TemporaryLibrary, PapisRunner


@pytest.mark.skipif(
    not shutil.which("git"),
    reason="Test requires 'git' executable to be in the PATH")
def test_git_cli(tmp_library: TemporaryLibrary) -> None:
    from papis.commands.git import cli
    cli_runner = PapisRunner()

    result = cli_runner.invoke(
        cli,
        ["init"])
    assert result.exit_code == 0

    folder, = papis.config.get_lib_dirs()
    assert os.path.exists(os.path.join(folder, ".git"))
