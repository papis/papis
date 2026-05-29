from __future__ import annotations

import shutil

from papis.testing import PapisRunner, TemporaryConfiguration, TemporaryLibrary


def test_no_config_shows_init_hint(tmp_config: TemporaryConfiguration) -> None:
    import papis.config
    from papis.commands.default import run as cli

    shutil.rmtree(tmp_config.configdir)
    papis.config.reset_configuration()

    cli_runner = PapisRunner()
    result = cli_runner.invoke(cli, ["list"])

    assert result.exit_code == 0
    assert "No configuration file exists at" in result.output
    assert "papis init" in result.output


def test_default_cli(tmp_library: TemporaryLibrary) -> None:
    from papis import __version__
    from papis.commands.default import run as cli

    cli_runner = PapisRunner()
    result = cli_runner.invoke(
        cli,
        ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.output

    result = cli_runner.invoke(
        cli,
        ["--set", "something", "42"])
    # error missing command
    assert result.exit_code == 2
