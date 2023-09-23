import re
import tempfile

from papis.testing import TemporaryLibrary, PapisRunner


def test_explore_cli(tmp_library: TemporaryLibrary) -> None:
    from papis.commands.explore import cli
    cli_runner = PapisRunner()

    result = cli_runner.invoke(
        cli,
        ["cmd", "ls"])
    assert result.exit_code == 0

    result = cli_runner.invoke(
        cli,
        ["lib", "krishnamurti"])
    assert result.exit_code == 0


def test_explore_bibtex_cli(tmp_library: TemporaryLibrary) -> None:
    from papis.commands.explore import cli
    cli_runner = PapisRunner()

    with tempfile.NamedTemporaryFile(delete=False, dir=tmp_library.tmpdir) as f:
        path = f.name

    result = cli_runner.invoke(
        cli,
        ["lib", "krishnamurti", "export", "--format", "bibtex", "--out", path])
    assert result.exit_code == 0

    with open(path) as fd:
        exported_bibtex = fd.read()

    assert exported_bibtex == (
        "@article{FreedomFromThJKri2009,\n"
        "  author = {J. Krishnamurti},\n"
        "  title = {Freedom from the known},\n"
        "  year = {2009},\n"
        "}"
    )


def test_explore_yaml_cli(tmp_library: TemporaryLibrary) -> None:
    from papis.commands.explore import cli
    cli_runner = PapisRunner()

    with tempfile.NamedTemporaryFile(delete=False, dir=tmp_library.tmpdir) as f:
        path = f.name

    result = cli_runner.invoke(
        cli,
        ["lib", "popper", "export", "--format", "yaml", "--out", path])
    assert result.exit_code == 0

    with open(path) as fd:
        exported_yaml = fd.read()

    assert re.match(
        "author: K. Popper\n"
        "doi: 10.1021/ct5004252\n"
        "papis_id: .*\n"
        "title: The open society\n"
        "volume: I\n",
        exported_yaml
    )


def test_explore_citations_and_json_cli(tmp_library: TemporaryLibrary) -> None:
    from papis.commands.explore import cli
    cli_runner = PapisRunner()

    with tempfile.NamedTemporaryFile(delete=False, dir=tmp_library.tmpdir) as f:
        path = f.name

    result = cli_runner.invoke(
        cli,
        ["citations", "krishnamurti", "export", "--format", "json", "--out", path])
    assert result.exit_code == 0

    with open(path) as fd:
        exported_json = fd.read()

    assert exported_json == "[]"
