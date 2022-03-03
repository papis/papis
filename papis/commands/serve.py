import click
import re
import os
import json
import logging
import http.server
import urllib.parse
from typing import Any, List, Optional, Union, Tuple
import functools
import cgi

import papis.api
import papis.cli
import papis.config
import papis.document
import papis.commands.add
import papis.commands.update
import papis.commands.export
import papis.crossref


logger = logging.getLogger("papis:server")


USE_GIT = False  # type: bool
TAGS_SPLIT_RX = re.compile(r"\s*[,\s]\s*")
HEADER_TEMPLATE = """
<head>
<title>{placeholder} Papis web</title>
<meta charset='UTF-8'>
<meta name='apple-mobile-web-app-capable' content='yes'>
<meta name='viewport' content='width=device-width, initial-scale=1'>
<link
  rel="stylesheet"
  href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"
  integrity="sha512-9usAa10IRO0HhonpyAIVpjrylPvoDwiPUiKdWk5t3PyolY1cOd4DSE0Ga+ri4AuTroPR5aQvXU9xC6qOPnzFeg=="
  crossorigin="anonymous" referrerpolicy="no-referrer" />
<link
  href='https://cdn.jsdelivr.net/npm/bootstrap@5.1.1/dist/css/bootstrap.min.css'
  rel='stylesheet'
  integrity='sha384-F3w7mX95PdgyTmZZMECAngseQB83DfGTowi0iMjiWaeVhAn4FJkqJByhZMI3AhiU'
  crossorigin='anonymous'>
<script
  src='https://cdn.jsdelivr.net/npm/bootstrap@5.1.1/dist/js/bootstrap.bundle.min.js'
  integrity='sha384-/bQdsTh/da6pkI1MST/rWKFNjaCP5gBSY4sEBT38Q/9RBh9AH40zEOg7Hlq2THRZ'
  crossorigin='anonymous'></script>
<script type="text/javascript" src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
<link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/1.11.4/css/jquery.dataTables.css">
<script type="text/javascript" charset="utf8" src="https://cdn.datatables.net/1.11.4/js/jquery.dataTables.js"></script>
</head>
"""  # noqa: E501

NAVBAR_TEMPLATE = """
<nav class="navbar navbar-expand-md navbar-light bg-light">
  <div class="container-fluid">
    <a class="navbar-brand" href="#">Papis</a>
    <button class="navbar-toggler"
            type="button"
            data-bs-toggle="collapse"
            data-bs-target="#navbarNav"
            aria-controls="navbarNav"
            aria-expanded="false"
            aria-label="Toggle navigation">
      <span class="navbar-toggler-icon"></span>
    </button>
    <div class="collapse navbar-collapse" id="navbarNav">
      <ul class="navbar-nav">
        <li class="nav-item">
          <a class="nav-link active"
             aria-current="page"
             href="/library/{libname}">
            All
         </a>
        </li>
        <li class="nav-item">
          <a class="nav-link"
             href="/library/{libname}/tags">
            Tags
          </a>
        </li>
        <li class="nav-item">
          <a class="nav-link"
             href="/libraries">
            Libraries
          </a>
        </li>
        <li class="nav-item">
          <a class="nav-link"
             href="#">
            Explore
          </a>
        </li>
      </ul>
    </div>
  </div>
</nav>
"""


INDEX_TEMPLATE = (
    """
    <html>
    """
    + HEADER_TEMPLATE +
    """
    <body>
    """
    + NAVBAR_TEMPLATE +
    """
        <div class="container">
            <h1>
                Papis library: <code>{libname}</code>
            </h1>
            <h3>
            <form action="/library/{libname}/query" method="GET">
                <input class="form-control"
                       type="text"
                       name="q"
                       placeholder="{placeholder}">
            </form>
            </h3>
            <table border="1" class="display" id="pub_table">
                <thead style='display:none;'>
                    <tr style="text-align: right;">
                    <th>info</th>
                    <th>data</th>
                    </tr>
                </thead>
                <tbody>
                    {documents}
                </tbody>
            </table>
        </div>
        <script type="text/javascript">
            $(document).ready(function(){{
                $('#pub_table').DataTable( {{
                    "bSort": false
                }} )
            ;}});
            </script>'
    </body>
</html>
""")


TAGS_PAGE = (
    """
    <html>
    """
    + HEADER_TEMPLATE +
    """
    <body>
    """
    + NAVBAR_TEMPLATE +
    """
        <div class="container">
            <h1>
                TAGS
            </h1>
            <div class="container">
                {tags}
            </div>
        </div>
    </body>
</html>
    """)


def render_navbar(libname: str, placeholder: str = "") -> str:
    return NAVBAR_TEMPLATE.format(**locals())


def render_files(files: List[str], libname: str, libfolder: str) -> str:
    return ("\n"
            .join("""
                  <a class='fa fa-file' href="/library/{libname}/file/{0}">
                  </a>
                  """
                  .format(k.replace(libfolder + "/", ""),
                          libname=libname)
                  for k in files))


def render_libraries() -> str:
    libs = papis.api.get_libraries()
    return ("<html>"
            + HEADER_TEMPLATE
            + """
                <body>
              """
            + render_navbar(libs[0])
            + """
                <div class="container">
                <h1>Library selection</h1>
                <ol class="list-group">
              """
            + "\n".join(
                """
                <a href="/library/{0}"
                   class="list-group-item list-group-item-action">
                    <i class="fa fa-book"></i>
                    {0}
                </a>
                """.format(lib) for lib in libs)
            + "</ol></body>"
            )


def render_document(libname: str, doc: papis.document.Document) -> str:
    return ("<html>"
            + HEADER_TEMPLATE.format(placeholder="")
            + """
                <body>
              """
            + render_navbar(libname, doc["ref"])
            + """
                <div class="container">
                <h1>{doc[title]}</h1>
                <h3>{doc[author]:.80}</h3>
                <form method="POST"
                      action="/library/{libname}/document/ref:{doc[ref]}">
                <input type="submit" class="form-control button">
                </input>
                <ol class="list-group">
              """.format(doc=doc, libname=libname)
            + "\n".join(
                 """
                 <li class="list-group-item">
                 <div class="form-floating">
                 <textarea class="form-control"
                           placeholder="{val}"
                           name="{key}"
                           id="{key}"
                           style="height: 100px">{val}</textarea>
                 <label for="{key}">{key}</label>
                 </div>

                 </li>
                 """.format(key=key, val=val)
                 for key, val in doc.items()
                 if not isinstance(val, list) or isinstance(val, dict)
                )
            + "</ol></form></body>"
            )


def get_tag_list(tags: Union[str, List[str]]) -> List[str]:
    if isinstance(tags, list):
        return tags
    else:
        return TAGS_SPLIT_RX.split(tags)


def render_tag(tag: str, libname: str) -> str:
    return """
    <a class="badge bg-dark papis-tag"
       href="/library/{libname}/query?q=tags:{0}">
        {0}
    </a>
    """.format(tag, libname=libname)


def render_document_item(libname: str,
                         libfolder: str,
                         doc: papis.document.Document) -> str:

    def render_if_doc_has(key: str,
                          fmt: str,
                          default: str = "",
                          **kws: Any) -> str:
        if key in doc:
            return fmt.format(doc=doc, **kws)
        else:
            return default.format(doc=doc, **kws)

    tag_renderer = functools.partial(render_tag, libname=libname)

    return (("""<tr><td>
                  <div class="ms-2 me-auto">
                    <div class="fw-bold">{doc[title]}</div>
                      {doc[author]}<br>
             """.format(doc=doc))
            + render_if_doc_has("journal",
                                """<i class="fa fa-book-open"></i>
                                {doc[journal]} <br>
                                """)
            + render_if_doc_has("files",
                                "{files}",
                                files=render_files(doc.get_files(),
                                                   libname,
                                                   libfolder))
            + """
                </td>
                <td>
              """
            + render_if_doc_has("tags",
                                """
                                <span class="papis-tags">
                                <i class="fa fa-tag"></i>
                                {tags}
                                </span></br>
                                """,
                                tags="".join(map(tag_renderer,
                                                 get_tag_list(doc["tags"]))))
            + render_if_doc_has("year",
                                """
                                <span class="badge bg-primary papis-year">
                                {doc[year]}
                                </span>
                                """,
                                default="""
                                <span class="badge bg-danger papis-year">
                                    ????
                                </span>
                                """)
            + render_if_doc_has("ref",
                                """
                                <a class="badge bg-dark" \
                            href="/library/{libname}/document/ref:{doc[ref]}">
                                    {doc[ref]}
                                </a>
                                """,
                                libname=libname)
            + """<ul class="list-group list-group-horizontal">"""
            + render_if_doc_has("url",
                                """
                                <a href="{doc[url]}"
                                   class="list-group-item \
                                          list-group-item-action"
                                   target="_blank">
                                    url
                                </a>
                                """)
            + render_if_doc_has("doi",
                                """
                                <a href="https://doi.org/{doc[doi]}"
                                    class="list-group-item \
                                           list-group-item-action"
                                    target="_blank">
                                    doi
                                </a>
                                <a
                             href="https://ui.adsabs.harvard.edu/abs/{doc[doi]}"
                                    class="list-group-item
                                           list-group-item-action"
                                    target="_blank">
                                    ads
                                </a>
                                <a
            href="https://ui.adsabs.harvard.edu/abs/{doc[doi]}/exportcitation"
                                    class="list-group-item \
                                           list-group-item-action"
                                    target="_blank">
                                    ads/cit
                                </a>
                                """)
            + """
                </ul>
            </td></tr>
            </li>
            """)


def render_index(docs: List[papis.document.Document],
                 libname: str,
                 placeholder: str = "query") -> str:
    libfolder = papis.config.get_lib_from_name(libname).paths[0]
    documents = "\n".join(render_document_item(libname, libfolder, d)
                          for d in docs)
    return (INDEX_TEMPLATE
            .format(documents=documents,
                    placeholder=placeholder,
                    libname=libname))


class PapisRequestHandler(http.server.BaseHTTPRequestHandler):

    def log_message(self, fmt: str, *args: Any) -> None:
        logger.info(fmt, *args)

    def _ok(self) -> None:
        self.send_response(200)

    def _header_json(self) -> None:
        self.send_header("Content-Type", "application/json")

    def _header_html(self) -> None:
        self.send_header("Content-Type", "text/html")

    def _send_json(self, data: Any) -> None:
        d = json.dumps(data)
        self.wfile.write(bytes(d, "utf-8"))

    def _send_json_error(self, code: int, msg: str) -> None:
        self.send_response(400)
        self._header_json()
        self.end_headers()
        self._send_json({"message": msg})

    def page_query(self, libname: str, query: str) -> None:
        docs = papis.api.get_documents_in_lib(libname, query)
        self.page_main(libname, docs)

    def page_main(self,
                  libname: Optional[str] = None,
                  docs: List[papis.document.Document] = []) -> None:
        self.send_response(200)
        self._header_html()
        self.end_headers()
        libname = libname or papis.api.get_lib_name()
        docs = docs or papis.api.get_all_documents_in_lib(libname)
        page = render_index(docs, libname)
        self.wfile.write(bytes(page, "utf-8"))
        self.wfile.flush()

    def page_tags(self, libname: Optional[str] = None) -> None:
        self.send_response(200)
        self._header_html()
        self.end_headers()

        libname = libname or papis.api.get_lib_name()
        docs = papis.api.get_all_documents_in_lib(libname)
        tags_of_tags = [get_tag_list(d["tags"]) for d in docs]
        tags = sorted(set(tag
                          for _tags in tags_of_tags
                          for tag in _tags))
        tag_renderer = functools.partial(render_tag, libname=libname)
        page = TAGS_PAGE.format(tags="".join(map(tag_renderer, tags)),
                                libname=libname,
                                placeholder="tags")
        self.wfile.write(bytes(page, "utf-8"))
        self.wfile.flush()

    def page_libraries(self) -> None:
        self.send_response(200)
        self._header_html()
        self.end_headers()

        page = render_libraries()
        self.wfile.write(bytes(page, "utf-8"))
        self.wfile.flush()

    def page_document(self, libname: str, ref: str) -> None:
        self.send_response(200)
        self._header_html()
        self.end_headers()

        docs = papis.api.get_documents_in_lib(libname, ref)
        if len(docs) > 1:
            raise Exception("More than one document match %s", ref)
        elif len(docs) == 0:
            raise Exception("No document found with ref %s", ref)

        page = render_document(libname, docs[0])
        self.wfile.write(bytes(page, "utf-8"))
        self.wfile.flush()

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
        self._send_json(dict(name=lib.name, paths=lib.paths))

    def get_all_documents(self, libname: str) -> None:
        docs = papis.api.get_all_documents_in_lib(libname)
        self.serve_documents(docs)

    def get_query(self, libname: str, query: str) -> None:
        cleaned_query = urllib.parse.unquote(query)
        logger.info("Querying in lib %s for <%s>", libname, cleaned_query)
        docs = papis.api.get_documents_in_lib(libname, cleaned_query)
        self.serve_documents(docs)

    def serve_documents(self, docs: List[papis.document.Document]) -> None:
        """
        Serve a list of documents and set the files attribute to
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

    def redirect(self, url: str, code: int = 301) -> None:
        page = ("""
                  <head>
                     <meta http-equiv="Refresh" content="0; URL={url}">
                  </head>
                """.format(url=url))
        self.send_response(code)
        self._header_html()
        self.end_headers()
        self.wfile.write(bytes(page, "utf-8"))
        self.wfile.flush()

    def get_document_format(self, libname: str, query: str, fmt: str) -> None:
        docs = papis.api.get_documents_in_lib(libname, query)
        fmts = papis.commands.export.run(docs, fmt)

        self._ok()
        self._header_json()
        self.end_headers()
        self._send_json(fmts)

    def send_local_document_file(self, libname: str, localpath: str) -> None:
        libfolder = papis.config.get_lib_from_name(libname).paths[0]
        path = os.path.join(str(libfolder), localpath)
        print(libname)
        print(localpath)
        print(libfolder)
        print(path)
        if os.path.exists(path):
            self._ok()
            self.send_header("Content-Type", "application/pdf")
            self.end_headers()
            with open(path, "rb") as f:
                self.wfile.write(f.read())
            self.wfile.flush()
        else:
            raise Exception("File {} does not exist".format(path))

    def do_ROUTES(self, routes: List[Tuple[str, Any]]) -> None:
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
                                  "Server path {0} not understood"
                                  .format(self.path))

    def update_page_document(self, libname: str, ref: str) -> None:
        global USE_GIT
        db = papis.database.get(libname)
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,  # type: ignore
            environ={'REQUEST_METHOD': 'POST'}
        )
        docs = db.query_dict(dict(ref=ref))
        if not docs:
            raise Exception("Document with ref %s not "
                            "found in the database" % ref)
        doc = docs[0]
        result = dict()
        for key in form:
            result[key] = form.getvalue(key)
        papis.commands.update.run(doc, result, git=USE_GIT)
        back_url = self.headers.get("Referer", "/library")
        self.redirect(back_url)

    def do_POST(self) -> None:
        routes = [
            ("^/library/?([^/]+)?/document/ref:(.*)$",
                self.update_page_document),
        ]
        self.do_ROUTES(routes)

    def do_GET(self) -> None:
        routes = [
            # html serving
            ("^/$",
                functools.partial(self.redirect, "/library")),
            ("^/library/?([^/]+)?$",
                self.page_main),
            ("^/libraries$",
                self.page_libraries),
            ("^/library/?([^/]+)?/query[?]q=(.*)$",
                self.page_query),
            ("^/library/?([^/]+)?/document/(ref:.*)$",
                self.page_document),
            ("^/library/([^/]+)/tags$",
                self.page_tags),
            ("^/library/([^/]+)/file/(.+)$",
                self.send_local_document_file),
            ("^/api/library$",
                self.get_libraries),

            # JSON API
            ("^/api/library/([^/]+)$",
                self.get_library),
            ("^/api/library/([^/]+)/document$",
                self.get_all_documents),
            ("^/api/library/([^/]+)/document/([^/]+)$",
                self.get_query),
            ("^/api/library/([^/]+)/document/([^/]+)/format/([^/]+)$",
                self.get_document_format),
        ]
        self.do_ROUTES(routes)


@click.command('serve')
@click.help_option('-h', '--help')
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
    logger.info("starting server in address http://%s:%s",
                address or "localhost",
                port)
    logger.info("press Ctrl-C to exit")
    logger.info("THIS COMMAND IS EXPERIMENTAL, "
                "expect bugs, feedback appreciated")
    httpd = http.server.HTTPServer(server_address, PapisRequestHandler)
    httpd.serve_forever()
