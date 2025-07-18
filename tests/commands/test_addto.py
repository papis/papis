import os
import papis.database

from papis.testing import TemporaryLibrary, PapisRunner

PDF_URL = "https://pdfa.org/download-area/smallest-possible-pdf/smallest-possible-pdf-2.0.pdf"
PDF_URL_BASE = "smallest-possible-pdf-2.0"
BAD_PDF_URL = "http://example.com/some/nonexisting/pdf/file.pdf"


def test_addto_run_no_files(tmp_library: TemporaryLibrary) -> None:
    import papis.config

    papis.config.set("add-file-name", "{doc[author]}-{doc[title]}")

    from papis.commands.addto import run

    db = papis.database.get()
    doc, = db.query_dict({"author": "popper"})
    assert len(doc.get_files()) == 0

    inputfile = tmp_library.create_random_file("pdf")
    run(doc, [inputfile])

    files = doc.get_files()
    assert len(files) == 1
    assert os.path.basename(files[0]) == "k.-popper-the-open-society.pdf"


def test_addto_run(tmp_library: TemporaryLibrary, nfiles: int = 5) -> None:
    from papis.commands.addto import run

    db = papis.database.get()
    doc, = db.query_dict({"author": "krishnamurti"})

    inputfiles = [tmp_library.create_random_file("pdf")
                  for i in range(nfiles)]

    nfiles_before = len(doc.get_files())
    run(doc, inputfiles)
    nfiles_after = len(doc.get_files())
    assert nfiles_after == nfiles_before + nfiles


def test_addto_cli(tmp_library: TemporaryLibrary, nfiles: int = 5) -> None:
    from papis.commands.addto import cli

    inputfiles = [tmp_library.create_random_file("pdf")
                  for i in range(nfiles)]

    cli_runner = PapisRunner()
    result = cli_runner.invoke(cli, sum([
        ["--files", f] for f in inputfiles
        ], []) + ["author:krishnamurti"])
    assert result.exit_code == 0

    db = papis.database.get()
    doc, = db.query_dict({"author": "krishnamurti"})
    files = [os.path.basename(f) for f in doc.get_files()][-nfiles:]

    from papis.paths import normalize_path

    def eq(outfile: str, infile: str) -> bool:
        outfile, _ = os.path.splitext(os.path.basename(outfile))
        infile, _ = os.path.splitext(os.path.basename(infile))
        return outfile.startswith(normalize_path(infile))

    assert all(eq(outfile, infile) for outfile, infile in zip(files, inputfiles)), (
        list(zip(files, inputfiles)))


def test_addto_cli_urls(tmp_library: TemporaryLibrary) -> None:
    from papis.commands.addto import cli

    db = papis.database.get()
    doc, = db.query_dict({"author": "popper"})
    assert len(doc.get_files()) == 0

    inputfile = tmp_library.create_random_file("pdf")

    cli_runner = PapisRunner()
    result = cli_runner.invoke(cli, ["--files", inputfile] + ["--urls", PDF_URL] + ["author:popper"])
    assert result.exit_code == 0

    db = papis.database.get()
    doc, = db.query_dict({"author": "popper"})
    files = [os.path.basename(f) for f in doc.get_files()]

    assert len(files) == 2

    # print(f"author:popper files: {files!r}")

    input_base, _ = os.path.splitext(os.path.basename(inputfile))
    for f in files:
        outfile, _ = os.path.splitext(os.path.basename(f))
        assert outfile.startswith(PDF_URL_BASE) or outfile.startswith(input_base)


def test_addto_cli_badfiles(tmp_library: TemporaryLibrary, nfiles: int = 5) -> None:

    db = papis.database.get()
    doc, = db.query_dict({"author": "popper"})
    assert len(doc.get_files()) == 0

    from papis.commands.addto import cli

    inputfiles = [tmp_library.create_random_file("pdf")
                  for _i in range(nfiles)]

    cli_runner = PapisRunner()
    args = (["--files", "/path/to/nonexistant/file.pdf"] + sum([
        ["--files", f] for f in inputfiles
        ], []) + ["--urls", PDF_URL] + ["--urls", BAD_PDF_URL])
    result = cli_runner.invoke(cli, args + ["author:popper"])
    assert result.exit_code == 0

    db = papis.database.get()
    doc, = db.query_dict({"author": "popper"})
    files = [os.path.basename(f) for f in doc.get_files()]

    assert len(files) == (nfiles + 1)
