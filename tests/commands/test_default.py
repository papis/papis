from papis.testing import PapisRunner, TemporaryLibrary


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
