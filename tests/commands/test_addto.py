import os
import papis.database
import logging
import pytest

from papis.testing import TemporaryLibrary, PapisRunner, create_random_file

from typing import Optional, Dict, Any

PDF_URL = "http://example.com/single-page-test.pdf"
PDF_URL_BASE = "single-page-test.pdf"
BAD_PDF_URL = "http://example.com/some/nonexisting/pdf/file.pdf"


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


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


def _mock_download_document(
        url: str,
        expected_document_extension: Optional[str] = None,
        _cookies: Optional[Dict[str, Any]] = None,
        filename: Optional[str] = None,
        ) -> Optional[str]:
    # certain markers in the url signal the failure case
    if "fail" in url or "nonexist" in url:
        return None

    suffix = None
    if expected_document_extension:
        filetype = expected_document_extension
        suffix = "." + expected_document_extension
    elif filename:
        _, filetype = os.path.splitext(os.path.basename(filename))
    else:
        filetype = url.split(".")[-1]

    if filename:
        prefix = filename
    else:
        prefix = url.split("/")[-1]

    return create_random_file(filetype=filetype, prefix=prefix, suffix=suffix)


# @pytest.mark.skipif(sys.platform.startswith("win"), reason="doesn't work on windows")
def test_addto_cli_urls(tmp_library: TemporaryLibrary,
                        monkeypatch: pytest.MonkeyPatch) -> None:
    from papis.commands.addto import cli

    db = papis.database.get()
    doc, = db.query_dict({"author": "popper"})
    assert len(doc.get_files()) == 0

    input_base = "poppler-test-pdf"
    inputfile = tmp_library.create_random_file("pdf", input_base)

    with monkeypatch.context() as mp:
        mp.setattr("papis.downloaders.download_document", _mock_download_document)
        cli_runner = PapisRunner()
        args = ["--files", inputfile, "--urls", PDF_URL, "author:popper"]
        result = cli_runner.invoke(cli, args)
        assert result.exit_code == 0

    db = papis.database.get()
    doc, = db.query_dict({"author": "popper"})
    files = [os.path.basename(f) for f in doc.get_files()]

    logger.debug("author:popper files: %r", files)
    assert len(files) == 2

    for f in files:
        logger.debug("got file: %r", f)
        outfile, _ = os.path.splitext(os.path.basename(f))
        logger.debug("(previously) checking file %r with file prefix %r", f, outfile)
        outfile = os.path.basename(f)
        logger.debug("checking file %r with file prefix %r", f, outfile)
        assert PDF_URL_BASE in outfile or input_base in outfile


def test_addto_cli_badfiles(tmp_library: TemporaryLibrary,
                            monkeypatch: pytest.MonkeyPatch,
                            nfiles: int = 5) -> None:

    db = papis.database.get()
    doc, = db.query_dict({"author": "popper"})
    assert len(doc.get_files()) == 0

    from papis.commands.addto import cli

    inputfiles = [tmp_library.create_random_file("pdf")
                  for _i in range(nfiles)]

    with monkeypatch.context() as mp:
        mp.setattr("papis.downloaders.download_document", _mock_download_document)
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
