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

    with open(path, encoding="utf-8") as fd:
        exported_bibtex = fd.read()

    assert exported_bibtex == (
        "@article{Freedom_from_th_J_Kri_2009,\n"
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

    with open(path, encoding="utf-8") as fd:
        exported_yaml = fd.read()

    assert re.match(
        r"author: K. Popper\n"
        r"doi: 10.1021/ct5004252\n"
        r"papis_id: .*\n"
        r"title: The open society\n"
        r"volume: I\n",
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

    with open(path, encoding="utf-8") as fd:
        exported_json = fd.read()

    assert exported_json == "[]"
