import papis.utils
from papis.document import from_data
from papis.testing import PapisRunner, TemporaryLibrary


def test_browse_run(tmp_library: TemporaryLibrary) -> None:
    from papis.commands.browse import run

    papis.config.set("browse-key", "url")
    assert run(from_data({"url": "hello.com"}), browse=False) == "hello.com"

    papis.config.set("browse-key", "doi")
    assert (
        run(from_data({"doi": "12312/1231"}), browse=False)
        == "https://doi.org/12312/1231")

    papis.config.set("browse-key", "isbn")
    assert (
        run(from_data({"isbn": "12312/1231"}), browse=False)
        == "https://isbnsearch.org/isbn/12312/1231")

    papis.config.set("browse-key", "nonexistentkey")
    assert (
        run(from_data({"title": "blih", "author": "me"}), browse=False)
        == "https://duckduckgo.com/?q=blih+me")


def test_browse_cli(tmp_library: TemporaryLibrary) -> None:
    from papis.commands.browse import cli

    cli_runner = PapisRunner()
    result = cli_runner.invoke(
        cli,
        ["--key", "doi", "--print", "popper"])
    assert result.exit_code == 0
    assert "doi.org" in result.output
    assert "10.1021/ct5004252" in result.output

    result = cli_runner.invoke(
        cli,
        ["__no_document__"])
    assert result.exit_code == 0
    assert not result.output

    result = cli_runner.invoke(
        cli,
        ["--key", "doi", "--print", "--all"])
    assert result.exit_code == 0
    assert result.output
