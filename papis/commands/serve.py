import click
import re
import os
import json
import logging
import http.server
import urllib.parse
from typing import Any, List
import functools

import papis.api
import papis.config
import papis.document
import papis.commands.add
import papis.commands.export
import papis.crossref


logger = logging.getLogger("papis:server")


class PapisRequestHandler(http.server.BaseHTTPRequestHandler):

    def log_message(self, fmt: str, *args: Any) -> None:
        logger.info(fmt, *args)

    def _ok(self) -> None:
        self.send_response(200)

    def _header_json(self) -> None:
        self.send_header("Content-Type", "application/json")

    def _send_json(self, data: Any) -> None:
        d = json.dumps(data)
        self.wfile.write(bytes(d, "utf-8"))

    def _send_json_error(self, code: int, msg: str) -> None:
        self.send_response(400)
        self._header_json()
        self.end_headers()
        self._send_json({"message": msg})

    def do_POST(self) -> None:
        return

    def get_libraries(self) -> None:
        logger.info("getting libraries")
        libs = papis.api.get_libraries()
        logger.debug("%s", libs)

        self._ok()
        self._header_json()
        self.end_headers()
        self._send_json(libs)

    def get_library(self, libname: str) -> None:
        logger.info(libname)
        lib = papis.config.get_lib_from_name(libname)

        self._ok()
        self._header_json()
        self.end_headers()
        self._send_json(lib.to_dict())

    def get_all_documents(self, libname: str) -> None:
        docs = papis.api.get_all_documents_in_lib(libname)
        self.serve_documents(docs)

    def get_query(self, libname: str, query: str) -> None:
        cleaned_query = urllib.parse.unquote(query)
        logger.info("Querying in lib %s for <%s>", libname, cleaned_query)
        docs = papis.api.get_documents_in_lib(libname, cleaned_query)
        self.serve_documents(docs)

    def serve_documents(self, docs: List[papis.document.Document]) -> None:
        """Serve a list of documents and set the files attribute to
        the full paths so that the user can reach them.
        """
        logger.info("serving %s documents", len(docs))

        # get absolute paths for files
        for d in docs:
            d["files"] = d.get_files()

        self._ok()
        self._header_json()
        self.end_headers()
        self._send_json(docs)

    def get_document_format(self, libname: str, query: str, fmt: str) -> None:
        docs = papis.api.get_documents_in_lib(libname, query)
        fmts = papis.commands.export.run(docs, fmt)

        self._ok()
        self._header_json()
        self.end_headers()
        self._send_json(fmts)

    def get_text_file(self, content_type: str, path: str) -> None:
        self._ok()
        self.send_header("Content-Type", content_type)
        self.end_headers()
        with open(path) as f:
            self.wfile.write(bytes(f.read(), "utf-8"))

    def get_local_resources(self, path) -> None:
        if os.path.exists(path):
            self._ok()
            self.send_header("Content-Type", "application/pdf")
            self.end_headers()
            with open(path, "rb") as f:
                self.wfile.write(f.read())
        else:
            raise Exception("File {} does not exist".format(path))

    def do_GET(self) -> None:
        routes = [
            ("^/$", functools.partial(self.get_text_file,
                                      "text/html; charset=utf-8",
                                      "index.html")),
            ("^/index.html$", functools.partial(self.get_text_file,
                                      "text/html; charset=utf-8",
                                      "index.html")),
            ("^/index.js$", functools.partial(self.get_text_file,
                                      "text/html; charset=utf-8",
                                      "index.js")),
            ("^/library$",
                self.get_libraries),
            ("^/library/([^/]+)$",
                self.get_library),
            ("^/library/([^/]+)/document$",
                self.get_all_documents),
            ("^/library/([^/]+)/document/([^/]+)$",
                self.get_query),
            ("^/library/([^/]+)/document/([^/]+)/format/([^/]+)$",
                self.get_document_format),
            ("^(.*)$", self.get_local_resources),
        ]
        try:
            for route, method in routes:
                m = re.match(route, self.path)
                if m:
                    method(*m.groups(), **m.groupdict())  # type: ignore
                    return
        except Exception as e:
            self._send_json_error(400, str(e))
        else:
            self._send_json_error(404,
                                  "Server path {0} not understood"
                                  .format(self.path))


@click.command('serve')
@click.help_option('-h', '--help')
@click.option("-p", "--port",
              help="Port to listen to",
              default=8888, type=int)
@click.option("--address", help="Address to bind", default="")
def cli(address: str, port: int) -> None:
    """Start a papis server"""
    server_address = (address, port)
    logger.info("starting server in address https://%s:%s",
                address or "localhost",
                port)
    logger.info("press Ctrl-C to exit")
    httpd = http.server.HTTPServer(server_address, PapisRequestHandler)
    httpd.serve_forever()
