import os
import tempfile

import papis.database
from papis.testing import PapisRunner, TemporaryLibrary


def test_export_run(tmp_library: TemporaryLibrary) -> None:
    from papis.commands.export import run

    db = papis.database.get()
    docs = db.get_all_documents()

    # bibtex
    exported_bibtex = run(docs, to_format="bibtex")
    assert exported_bibtex
    data = papis.bibtex.bibtex_to_dict(exported_bibtex)
    assert isinstance(data, list)
    assert len(data) == len(docs)

    # FIXME: not all fields are there and some don't match due to bibtex
    # pre- or post-processing
    assert all(d["title"] == doc["title"] for d, doc in zip(data, docs))

    # json
    exported_json = run(docs, to_format="json")
    assert exported_json

    import json
    data = json.loads(exported_json)
    assert isinstance(data, list)
    assert data == docs

    # yaml
    exported_yaml = run(docs, to_format="yaml")
    assert exported_yaml

    with tempfile.NamedTemporaryFile(
            "w+", delete=False, dir=tmp_library.tmpdir, encoding="utf-8"
            ) as fd:
        fd.write(exported_yaml)
        path = fd.name

    from papis.yaml import yaml_to_list
    data = yaml_to_list(path, raise_exception=True)
    assert data == docs


def test_export_json_cli(tmp_library: TemporaryLibrary) -> None:
    from papis.commands.export import cli
    cli_runner = PapisRunner()

    result = cli_runner.invoke(
        cli,
        ["--format", "json", "_this_document_does_not_exist_"])

    assert result.exit_code == 0
    assert not result.output

    result = cli_runner.invoke(
        cli,
        ["--format", "json", "krishnamurti"])
    assert result.exit_code == 0

    import json
    data = json.loads(result.output)

    assert len(data) == 1
    assert "Krishnamurti" in data[0]["author"]
    assert data[0]["year"] == 2009

    outfile = os.path.join(tmp_library.tmpdir, "test.json")
    result = cli_runner.invoke(
        cli,
        ["--format", "json", "--out", outfile, "krishnamurti"])

    assert result.exit_code == 0
    assert os.path.exists(outfile)

    with open(outfile, encoding="utf-8") as fd:
        data_out = json.load(fd)

    assert len(data_out) == 1
    assert data_out == data


def test_export_yaml_cli(tmp_library: TemporaryLibrary) -> None:
    from papis.commands.export import cli
    cli_runner = PapisRunner()

    result = cli_runner.invoke(
        cli,
        ["--format", "yaml", "krishnamurti"])
    assert result.exit_code == 0

    import yaml
    data = yaml.safe_load(result.output)

    assert "Krishnamurti" in data["author"]
    assert data["year"] == 2009

    outfile = os.path.join(tmp_library.tmpdir, "test.yaml")
    result = cli_runner.invoke(
        cli,
        ["--format", "yaml", "--out", outfile, "krishnamurti"])

    assert result.exit_code == 0
    assert os.path.exists(outfile)

    with open(outfile, encoding="utf-8") as fd:
        data_out = yaml.safe_load(fd)

    assert data_out == data


def test_export_bibtex_append(tmp_library: TemporaryLibrary) -> None:
    from papis.commands.export import cli, run

    db = papis.database.get()

    doc1 = db.query("krishnamurti")[0]
    doc2 = db.query("popper")[0]
    docs = [doc1, doc2]

    text = run(docs, to_format="bibtex")
    data = papis.bibtex.bibtex_to_dict(text)

    cli_runner = PapisRunner()
    outfile = os.path.join(tmp_library.tmpdir, "test.bib")

    result = cli_runner.invoke(
        cli,
        ["--append", "--format", "bibtex", "--out", outfile, "krishnamurti"])

    assert result.exit_code == 0
    assert os.path.exists(outfile)

    with open(outfile, encoding="utf-8") as fd:
        single_text = fd.read()

    single_data = papis.bibtex.bibtex_to_dict(single_text)
    assert len(single_data) == 1

    result = cli_runner.invoke(
        cli,
        ["--append", "--format", "bibtex", "--out", outfile, "popper"])

    assert result.exit_code == 0
    assert os.path.exists(outfile)

    with open(outfile, encoding="utf-8") as fd:
        appended_text = fd.read()

    appended_data = papis.bibtex.bibtex_to_dict(appended_text)
    assert len(appended_data) == len(data)

    # NOTE: The intention is that these will match, this is a problem to be
    # solved. On --append, formatting doesn't match because test.bib has no
    # newline at end-of-file.
    assert appended_text != text


def test_export_folder_cli(tmp_library: TemporaryLibrary) -> None:
    from papis.commands.export import cli
    cli_runner = PapisRunner()

    outdir = os.path.join(tmp_library.libdir, "test_export_subfolder")
    result = cli_runner.invoke(
        cli,
        ["--folder", "--out", outdir, "krishnamurti"])

    assert result.exit_code == 0
    assert os.path.exists(outdir)
    assert os.path.isdir(outdir)

    doc = papis.document.from_folder(outdir)
    assert doc is not None
    assert "Krishnamurti" in doc["author"]


def test_export_folder_all_cli(tmp_library: TemporaryLibrary) -> None:
    from papis.commands.export import cli
    cli_runner = PapisRunner()

    outdir = os.path.join(tmp_library.libdir, "test_export_folder")
    result = cli_runner.invoke(
        cli,
        ["--all", "--folder", "--out", outdir])

    assert result.exit_code == 0
    assert os.path.exists(outdir)
    assert os.path.isdir(outdir)

    import glob
    dirs = glob.glob(os.path.join(outdir, "*"))
    assert len(dirs) == 8

    for d in dirs:
        assert os.path.exists(d)
        assert os.path.isdir(d)
