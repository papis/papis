import re
import os
import json
import http.server
import urllib.parse
from typing import Any, List, Optional, Tuple, Callable, Dict

import functools
import collections
import tempfile

import click

import papis.api
import papis.cli
import papis.config
import papis.document
import papis.commands.add
import papis.commands.update
import papis.commands.export
import papis.commands.doctor
import papis.crossref
import papis.notes
import papis.citations
import papis.logging

logger = papis.logging.get_logger(__name__)

USE_GIT = False
TAGS_LIST: Dict[str, Optional[Dict[str, int]]] = {}


AnyFn = Callable[..., Any]


try:
    # NOTE: the cgi module is being removed in python 3.13, so we add our own
    # little copy of FieldStorage when it's not available
    from cgi import FieldStorage
except ImportError:
    from email.message import Message
    from dataclasses import dataclass, field
    from typing import IO, Iterator, Union

    @dataclass
    class MiniFieldStorage:
        name: str
        value: str

        def __repr__(self) -> str:
            return f"MiniFieldStorage({self.name!r}, {self.value!r})"

    @dataclass
    class FieldStorage:  # type: ignore[no-redef]
        # NOTE: fields taken from cgi.FieldStorage.__init__
        # https://github.com/python/cpython/blob/3.12/Lib/cgi.py#L330

        fp: Optional[IO[bytes]] = None
        headers: Union[Dict[str, str], Message] = field(default_factory=dict)
        outerboundary: bytes = b""
        environ: Dict[str, str] = field(default_factory=dict)
        keep_blank_values: bool = False
        strict_parsing: bool = False
        limit: Optional[int] = None
        encoding: str = "utf-8"
        errors: str = "replace"
        max_num_fields: Optional[int] = None
        separator: str = "&"

        def __post_init__(self) -> None:
            self.read_urlencoded()

        @property
        def length(self) -> int:
            return int(self.headers.get("content-length", -1))

        @property
        def qs_on_post(self) -> Optional[str]:
            return None

        def read_urlencoded(self) -> None:
            assert self.fp is not None

            qs_b = self.fp.read(self.length)
            if not isinstance(qs_b, bytes):
                raise ValueError(
                    f"'{self.fp}' should return bytes, got {type(qs_b).__name__}")

            qs = qs_b.decode(self.encoding, self.errors)
            if self.qs_on_post:
                qs += "&" + self.qs_on_post

            query = urllib.parse.parse_qsl(
                qs,
                self.keep_blank_values,
                self.strict_parsing,
                encoding=self.encoding,
                errors=self.errors,
                max_num_fields=self.max_num_fields,
                separator=self.separator)

            self.list = [MiniFieldStorage(key, value) for key, value in query]

        def getvalue(self, name: str) -> str:
            result = [fs for fs in self.list if fs.name == name]
            assert len(result) == 1

            return result[0].value

        def __iter__(self) -> Iterator[str]:
            return iter(self.keys())

        def keys(self) -> List[str]:
            return list({fs.name for fs in self.list})


# Decorators
def redirecting(to: str) -> AnyFn:
    """
    Decorator to redirect http requests easily.
    """
    def wrapper(fn: AnyFn) -> AnyFn:
        def wrapped(self: Any, *args: Any, **kwargs: Any) -> None:
            fn(self, *args, **kwargs)
            self.redirect(to)
        return wrapped
    return wrapper


def ok_html(fun: AnyFn) -> AnyFn:
    """
    Decorator to assert that the response is html code
    """
    def wrapped(self: Any, *args: Any, **kwargs: Any) -> Any:
        self.send_response(200)
        self.send_header_html()
        self.end_headers()
        return fun(self, *args, **kwargs)
    return wrapped


class PapisRequestHandler(http.server.BaseHTTPRequestHandler):

    """
    The main request handler of the Papis web application.
    """

    def log_message(self, fmt: str, *args: Any) -> None:
        logger.info(fmt, *args)

    def _ok(self) -> None:
        self.send_response(200)

    def _header_json(self) -> None:
        self.send_header("Content-Type", "application/json")

    def send_header_html(self) -> None:
        """
        Say that the content sent is html
        """
        self.send_header("Content-Type", "text/html")

    def _send_json(self, data: Any) -> None:
        data = json.dumps(data)
        self.wfile.write(bytes(data, "utf-8"))

    def _send_json_error(self, code: int, msg: str) -> None:
        self.send_response(code)
        self._header_json()
        self.end_headers()
        self._send_json({"message": msg})

    def page_query(self, libname: str, query: str) -> None:
        self._handle_lib(libname)
        cleaned_query = urllib.parse.unquote_plus(query)
        docs = papis.api.get_documents_in_lib(libname, cleaned_query)
        self.page_main(libname, docs, cleaned_query)

    def page_serve_all(self, libname: str) -> None:
        self._handle_lib(libname)
        docs = papis.api.get_all_documents_in_lib(libname)
        self.page_main(libname, docs, "All documents")

    def page_main(self,
                  libname: Optional[str] = None,
                  docs: Optional[List[papis.document.Document]] = None,
                  query: Optional[str] = None) -> None:
        import papis.web.search

        if docs is None:
            docs = []

        libname = libname or papis.api.get_lib_name()
        self._handle_lib(libname)

        self.send_response(200)
        self.send_header_html()
        self.end_headers()
        if len(docs) == 0:
            if papis.config.getboolean("serve-empty-query-get-all-documents"):
                docs = papis.api.get_all_documents_in_lib(libname)

        libfolder = papis.config.get_lib_from_name(libname).paths[0]
        placeholder = papis.web.search.QUERY_PLACEHOLDER
        page = papis.web.search.html(documents=docs,
                                     libname=libname,
                                     libfolder=libfolder,
                                     pretitle=query or "HOME",
                                     query=query or placeholder)
        self.wfile.write(bytes(str(page), "utf-8"))
        self.wfile.flush()

    @ok_html
    @redirecting("/library")
    def clear_cache(self, libname: str) -> None:
        self._handle_lib(libname)
        db = papis.database.get(libname)
        db.clear()
        db.initialize()

    @ok_html
    def page_tags(self, libname: Optional[str] = None,
                  sort_by: Optional[str] = None) -> None:
        import papis.web.tags

        global TAGS_LIST
        libname = libname or papis.api.get_lib_name()
        self._handle_lib(libname)
        docs = papis.api.get_all_documents_in_lib(libname)
        tags_of_tags = [tag
                        for d in docs
                        for tag in papis.web.tags.ensure_tags_list(d["tags"])]
        if TAGS_LIST.get(libname) is None:
            TAGS_LIST[libname] = collections.defaultdict(int)
            for tag in tags_of_tags:
                TAGS_LIST[libname][tag] += 1  # type: ignore[index]

        page = papis.web.tags.html(libname=libname,
                                   pretitle="TAGS",
                                   tags=TAGS_LIST[libname] or {},
                                   sort_by=sort_by or "")

        self.wfile.write(bytes(str(page), "utf-8"))
        self.wfile.flush()

    @ok_html
    def page_tags_refresh(self, libname: Optional[str] = None) -> None:
        libname = libname or papis.api.get_lib_name()
        self._handle_lib(libname)
        TAGS_LIST[libname] = None
        self.redirect(f"/library/{libname}/tags")

    @ok_html
    def page_libraries(self) -> None:
        import papis.web.libraries

        libname = papis.api.get_lib_name()
        page = papis.web.libraries.html(libname=libname)
        self.wfile.write(bytes(str(page), "utf-8"))
        self.wfile.flush()

    @ok_html
    def page_document(self, libname: str, papis_id: str) -> None:
        import papis.web.docview

        doc = self._get_document(libname, papis_id)
        page = papis.web.docview.html(libname=libname, doc=doc)
        self.wfile.write(bytes(str(page), "utf-8"))
        self.wfile.flush()

    @ok_html
    def fetch_citations(self, libname: str, papis_id: str) -> None:
        doc = self._get_document(libname, papis_id)
        papis.citations.fetch_and_save_citations(doc)
        self._redirect_back()

    @ok_html
    def fetch_cited_by(self, libname: str, papis_id: str) -> None:
        doc = self._get_document(libname, papis_id)
        papis.citations.fetch_and_save_cited_by_from_database(doc)
        self._redirect_back()

    def get_libraries(self) -> None:
        logger.info("Getting libraries.")
        libs = papis.api.get_libraries()
        logger.debug("Found libraries: '%s'.", "', '".join(libs))

        self._ok()
        self._header_json()
        self.end_headers()
        self._send_json(libs)

    def get_library(self, libname: str) -> None:
        logger.info("Getting library '%s'.", libname)
        lib = papis.config.get_lib_from_name(libname)

        self._ok()
        self._header_json()
        self.end_headers()
        self._send_json({"name": lib.name, "paths": lib.paths})

    def get_all_documents(self, libname: str) -> None:
        self._handle_lib(libname)
        docs = papis.api.get_all_documents_in_lib(libname)
        self.serve_documents(docs)

    def get_query(self, libname: str, query: str) -> None:
        self._handle_lib(libname)
        cleaned_query = urllib.parse.unquote(query)
        logger.info("Querying in library '%s' for '%s'.", libname, cleaned_query)
        docs = papis.api.get_documents_in_lib(libname, cleaned_query)
        self.serve_documents(docs)

    def serve_documents(self, docs: List[papis.document.Document]) -> None:
        """
        Serve a list of documents and set the files attribute to
        the full paths so that the user can reach them.
        """
        logger.info("Serving %s documents.", len(docs))

        # get absolute paths for files
        for d in docs:
            d["files"] = d.get_files()

        self._ok()
        self._header_json()
        self.end_headers()
        self._send_json(docs)

    def redirect(self, url: str, code: int = 301) -> None:
        page = (f"""
                  <head>
                     <meta http-equiv="Refresh" content="0; URL={url}">
                  </head>
                """)
        self.send_response(code)
        self.send_header_html()
        self.send_header("Location", url)
        self.end_headers()
        self.wfile.write(bytes(page, "utf-8"))
        self.wfile.flush()

    def _redirect_back(self) -> None:
        back_url = self.headers.get("Referer", "/library")
        self.redirect(back_url)

    def get_document_format(self, libname: str, query: str, fmt: str) -> None:
        docs = papis.api.get_documents_in_lib(libname, query)
        fmts = papis.commands.export.run(docs, fmt)

        self._ok()
        self._header_json()
        self.end_headers()
        self._send_json(fmts)

    def send_local_document_file(self, libname: str, localpath: str) -> None:
        libfolder = papis.config.get_lib_from_name(libname).paths[0]
        path = os.path.join(libfolder, localpath)
        if os.path.exists(path):
            self._ok()
            self.send_header("Content-Type", "application/pdf")
            self.end_headers()
            with open(path, "rb") as f:
                self.wfile.write(f.read())
            self.wfile.flush()
        else:
            raise FileNotFoundError(f"File '{path}' does not exist")

    def process_routes(self,
                       routes: List[Tuple[str, Any]]) -> None:
        """
        Performs the actions of the given routes and dispatches a 404
        page if there is an error.
        """
        try:
            for route, method in routes:
                m = re.match(route, self.path)
                if m:
                    method(*m.groups(), **m.groupdict())
                    return
        except Exception as e:
            self._send_json_error(400, str(e))
        else:
            self._send_json_error(404,
                                  f"Server path {self.path} not understood"
                                  )

    def _handle_lib(self, libname: str) -> None:
        papis.api.set_lib_from_name(libname)

    def _get_document(self,
                      libname: str,
                      papis_id: str) -> papis.document.Document:
        self._handle_lib(libname)
        db = papis.database.get(libname)
        doc = db.find_by_id(papis_id)
        if not doc:
            raise ValueError(
                f"Document with ref '{papis_id}' not found in the database"
                )
        return doc

    def _get_form(self, method: str = "POST") -> FieldStorage:
        return FieldStorage(fp=self.rfile,
                            headers=self.headers,
                            environ={"REQUEST_METHOD": method})

    def update_notes(self, libname: str, papis_id: str) -> None:
        doc = self._get_document(libname, papis_id)
        form = self._get_form("POST")
        new_notes = form.getvalue("value")
        notes_path = papis.notes.notes_path(doc)
        with open(notes_path, "w+") as fdr:
            fdr.write(new_notes)
        self._redirect_back()

    def update_info(self, libname: str, papis_id: str) -> None:
        """
        It updates the information by the provided form.

        It first checks that the yaml is readable by using
        yaml_to_data function. If it is successful it supposes
        it is a correct yaml, it overwrites the old yaml
        and updates the database and the document with it.
        """
        doc = self._get_document(libname, papis_id)
        form = self._get_form("POST")
        new_info = form.getvalue("value")
        info_path = doc.get_info_file()

        logger.info("Checking syntax of the info file: '%s'.", info_path)
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as fdr:
            fdr.write(new_info)
        try:
            papis.yaml.yaml_to_data(fdr.name, raise_exception=True)
        except ValueError as e:
            self._send_json_error(404, f"Error in info file: {e}")
            os.unlink(fdr.name)
            return
        else:
            os.unlink(fdr.name)
            logger.info("Info file is valid.")
            with open(info_path, "w+") as _fdr:
                _fdr.write(new_info)
            doc.load()
            papis.api.save_doc(doc)
            self._redirect_back()
            return

    def update_page_document(self, libname: str, papis_id: str) -> None:
        doc = self._get_document(libname, papis_id)
        form = self._get_form("POST")

        result = {}
        for key in form:
            if key == "newkey-name":
                newkey = str(form.getvalue("newkey-name"))
                newval = form.getvalue("newkey-value")
                result[newkey] = newval
            elif key == "newkey-value":
                pass
            else:
                result[key] = form.getvalue(key)
        papis.commands.update.run(document=doc,
                                  data=result,
                                  git=USE_GIT)
        self._redirect_back()

    def serve_static(self, static_path: str, params: str) -> None:
        import papis.web.static

        folders = papis.web.static.static_paths()
        partial_path = urllib.parse.unquote_plus(static_path)
        for folder in folders:
            path = os.path.join(folder, partial_path)
            if not os.path.exists(path):
                continue

            self._ok()
            if path.endswith("svg"):
                self.send_header("Content-Type", "image/svg+xml")
            elif path.endswith("pdf"):
                self.send_header("Content-Type", "application/pdf")
            elif path.endswith("png"):
                self.send_header("Content-Type", "image/png")
            elif path.endswith("gif"):
                self.send_header("Content-Type", "image/gif")

            self.end_headers()
            with open(path, "rb") as f:
                self.wfile.write(f.read())
                self.wfile.flush()
            return

        raise FileNotFoundError(f"File '{path}' does not exist")

    def do_POST(self) -> None:              # noqa: N802
        """
        HTTP POST route definitions
        """
        routes = [
            ("^/library/?([^/]+)?/document/([a-z0-9]+)$",
                self.update_page_document),
            ("^/library/?([^/]+)?/document/notes/([a-z0-9]+)$",
                self.update_notes),
            ("^/library/?([^/]+)?/document/info/([a-z0-9]+)$",
                self.update_info),
            ("^/library/?([^/]+)?/document/fetch-citations/([a-z0-9]+)$",
                self.fetch_citations),
            ("^/library/?([^/]+)?/document/fetch-cited-by/([a-z0-9]+)$",
                self.fetch_cited_by),
        ]
        self.process_routes(routes)

    def do_GET(self) -> None:               # noqa: N802
        """
        HTTP GET route definitions
        """
        routes = [
            # html serving
            ("^/$",
                functools.partial(self.redirect, "/library")),
            ("^/library/?([^/]+)?$",
                self.page_main),
            ("^/libraries$",
                self.page_libraries),
            ("^/library/?([^/]+)?/all$",
                self.page_serve_all),
            ("^/library/?([^/]+)?/query[?]q=(.*)$",
                self.page_query),
            ("^/library/?([^/]+)?/document/([a-z0-9]+)$",
                self.page_document),
            ("^/library/([^/]+)/tags(?:[?]sort=(.*))?$",
                self.page_tags),
            ("^/library/([^/]+)/tags/refresh$",
                self.page_tags_refresh),
            ("^/library/([^/]+)/file/(.+)$",
                self.send_local_document_file),
            ("^/library/([^/]+)/clear_cache$",
                self.clear_cache),
            ("^/static/([^?]*)(.*)$",
                self.serve_static),

            # JSON API
            ("^/api/library$",
                self.get_libraries),
            ("^/api/library/([^/]+)$",
                self.get_library),
            ("^/api/library/([^/]+)/document$",
                self.get_all_documents),
            ("^/api/library/([^/]+)/document/([^/]+)$",
                self.get_query),
            ("^/api/library/([^/]+)/document/([^/]+)/format/([^/]+)$",
                self.get_document_format),
        ]
        self.process_routes(routes)


@click.command("serve")
@click.help_option("-h", "--help")
@click.option("-p", "--port",
              help="Port to listen to",
              default=8888, type=int)
@papis.cli.git_option(help="Add changes made to the info file")
@click.option("--address",
              "--host",
              help="Address to bind",
              default="localhost")
def cli(address: str, port: int, git: bool) -> None:
    """
    Start a papis server
    """
    global USE_GIT
    USE_GIT = git
    server_address = (address, port)

    import papis.web.pdfjs

    if not papis.web.pdfjs.detect_pdfjs():
        logger.warning(papis.web.pdfjs.error_message())

    logger.info("Starting server in address 'http://%s:%s'.",
                address or "localhost",
                port)
    logger.info("Press <Ctrl-C> to exit.")
    logger.info("THIS COMMAND IS EXPERIMENTAL, expect bugs. Feedback appreciated!")

    httpd = http.server.HTTPServer(server_address, PapisRequestHandler)
    httpd.serve_forever()
