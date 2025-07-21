import os
import time
import papis.database
import logging
import pytest

from papis.testing import TemporaryLibrary, PapisRunner

# PDF_URL = "https://pdfa.org/download-area/smallest-possible-pdf/smallest-possible-pdf-2.0.pdf"  # noqa
PDF_URL = "http://localhost:8000/single-page-test.pdf"  # noqa
PDF_URL_BASE = "single-page-test.pdf"
BAD_PDF_URL = "http://localhost:8000/some/nonexisting/pdf/file.pdf"

PDF_RESOURCES = os.path.join(os.path.dirname(__file__), "..", "resources", "pdf")

__SERVER_THREAD = None

logger = logging.getLogger(__name__)


@pytest.fixture(autouse=True, scope="session")
def local_http_server() -> None:
    global __SERVER_THREAD
    if __SERVER_THREAD is not None:
        return

    logger = logging.getLogger(__name__)

    import threading
    from http.server import SimpleHTTPRequestHandler
    from socketserver import ThreadingTCPServer

    # Define the server address and port
    host = "localhost"
    port = 8000

    # Create a custom request handler
    class CustomHandler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):  # type: ignore
            super().__init__(*args, directory=PDF_RESOURCES, **kwargs)

        # Optionally, override methods like do_GET to customize behavior
        def do_GET(self) -> None: # noqa
            logger.debug("GET %s", self.path)
            # Add custom logic here if needed
            super().do_GET()

    # Start the server in a separate thread
    def run_http_server() -> None:
        for i in range(10):
            try:
                logger.debug("starting http server on %s:%d", host, port)
                with ThreadingTCPServer((host, port), CustomHandler) as httpd:
                    httpd.serve_forever()
                break
            except OSError as exc:
                logger.debug("failed to setup http server", exc_info=exc)
                if i == 10:
                    raise
                time.sleep(1)

    # potentially wait for the OS to make the port available.
    time.sleep(1)

    __SERVER_THREAD = threading.Thread(target=run_http_server)
    __SERVER_THREAD.daemon = True
    __SERVER_THREAD.start()

    # Optionally, you can add a small delay to ensure the server is up
    time.sleep(1)


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

    input_base = "poppler-test-pdf"
    inputfile = tmp_library.create_random_file("pdf", input_base)

    cli_runner = PapisRunner()
    args = ["--files", inputfile, "--urls", pdf_url, "author:popper"]
    result = cli_runner.invoke(cli, args)
    assert result.exit_code == 0

    db = papis.database.get()
    doc, = db.query_dict({"author": "popper"})
    files = [os.path.basename(f) for f in doc.get_files()]

    assert len(files) == 2

    # print(f"author:popper files: {files!r}")

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
