import os
import papis.database

from tests.testlib import TemporaryLibrary, PapisRunner


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

    from papis.utils import clean_document_name

    def eq(outfile: str, infile: str) -> bool:
        outfile, _ = os.path.splitext(os.path.basename(outfile))
        infile, _ = os.path.splitext(os.path.basename(infile))
        return outfile.startswith(clean_document_name(infile))

    assert all([eq(outfile, infile) for outfile, infile in zip(files, inputfiles)]), (
        list(zip(files, inputfiles)))
