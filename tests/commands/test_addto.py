import os
import papis.database

from papis.testing import TemporaryLibrary, PapisRunner


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

    from itertools import chain
    cli_runner = PapisRunner()
    result = cli_runner.invoke(cli, [
        *chain.from_iterable(["--files", f] for f in inputfiles),
        "author:krishnamurti"
        ])
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
