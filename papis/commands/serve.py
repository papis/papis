import re
import os
import json
import logging
import http.server
import urllib.parse
from typing import Any, List, Optional, Union, Tuple, Callable, Dict
import functools
import cgi
import collections

import click
import dominate.tags as t

import papis.api
import papis.cli
import papis.config
import papis.document
import papis.commands.add
import papis.commands.update
import papis.commands.export
import papis.crossref


logger = logging.getLogger("papis:server")

# types
HtmlGiver = Callable[[], t.html_tag]


USE_GIT = False  # type: bool
TAGS_SPLIT_RX = re.compile(r"\s*[,\s]\s*")
TAGS_LIST = {}  # type: Dict[str, Optional[Dict[str, int]]]
QUERY_PLACEHOLDER = "insert query..."
PAPIS_FILE_ICON_CLASS = "papis-file-icon"


def _fa(name: str, namespace: str = "fa") -> str:
    """
    Font awesome wrapper
    """
    return namespace + " fa-" + name


def _flex(where: str, cls: str = "", **kwargs: Any) -> t.html_tag:
    return t.div(cls=cls + " d-flex justify-content-" + where, **kwargs)


def _icon(name: str, namespace: str = "fa") -> t.html_tag:
    return t.i(cls=_fa(name, namespace=namespace))


def _container() -> t.html_tag:
    return t.div(cls="container")


def _modal(body: HtmlGiver, id: str) -> t.html_tag:
    with t.div(cls="modal fade", tabindex="-1", id=id) as rst:
        with t.div(cls="modal-dialog"):
            with t.div(cls="modal-content"):
                with t.div(cls="modal-body"):
                    body()
    return rst


def _header(pretitle: str, extra: Optional[t.html_tag] = None) -> t.html_tag:
    head = t.head()
    with head:
        t.title("{} Papis web".format(pretitle))
        t.meta(name="apple-mobile-web-app-capable", content="yes")
        t.meta(charset="UTF-8")
        t.meta(name="apple-mobile-web-app-capable", content="yes")
        t.meta(name="viewport", content="width=device-width, initial-scale=1")

        for awesome in papis.config.getlist("serve-font-awesome-css"):
            t.link(rel="stylesheet",
                   href=awesome,
                   crossorigin="anonymous",
                   referrerpolicy="no-referrer")
        t.link(href=papis.config.getstring("serve-bootstrap-css"),
               rel="stylesheet",
               crossorigin="anonymous")
        t.script(type="text/javascript",
                 src=papis.config.getstring("serve-bootstrap-js"),
                 crossorigin="anonymous")
        t.script(type="text/javascript",
                 src=papis.config.getstring("serve-jquery-js"))
        t.link(rel="stylesheet",
               type="text/css",
               href=papis.config.getstring("serve-jquery.dataTables-css"))
        t.script(type="text/javascript",
                 charset="utf8",
                 src=papis.config.getstring("serve-jquery.dataTables-js"))

        for href in papis.config.getlist("serve-user-css"):
            t.link(rel="stylesheet", type="text/css", href=href)

        for src in papis.config.getlist("serve-user-js"):
            t.script(type="text/javascript", src=src)

    if extra is not None:
        head.add(extra)

    return head


def _navbar(libname: str) -> t.html_tag:

    def _li(title: str, href: str, active: bool = False) -> t.html_tag:
        with t.li(cls="nav-item") as result:
            t.a(title,
                cls="nav-link" + (" active" if active else ""),
                aria_current="page",
                href=href)
        return result

    with t.nav(cls="navbar navbar-expand-md navbar-light bg-light") as nav:
        with t.div(cls="container-fluid"):

            t.a("Papis", href="#", cls="navbar-brand")

            but = t.button(cls="navbar-toggler",
                           type="button",
                           data_bs_toggle="collapse",
                           data_bs_target="#navbarNav",
                           aria_controls="navbarNav",
                           aria_expanded="false",
                           aria_label="Toggle navigation")
            with but:
                t.span(cls="navbar-toggler-icon")

            with t.div(id="navbarNav"):
                t.attr(cls="collapse navbar-collapse")
                with t.ul(cls="navbar-nav"):
                    _li("All", "/library/{libname}".format(libname=libname),
                        active=True)
                    _li("Tags",
                        "/library/{libname}/tags".format(libname=libname))
                    _li("Libraries", "/libraries")
                    _li("Explore", "#")

    return nav


def _clear_cache(libname: str) -> t.html_tag:
    result = t.a(href="/library/{libname}/clear_cache".format(libname=libname))
    with result:
        t.i(cls=_fa("refresh"),
            data_bs_toggle="tooltip",
            title="Clear Cache")
    return result


def _jquery_table(libname: str,
                  libfolder: str,
                  documents: List[papis.document.Document]) -> t.html_tag:
    script = """
    $(document).ready(function(){
        $('#pub_table').DataTable({'bSort': false});
    });
    """
    with t.table(border="1", cls="display", id="pub_table") as result:
        with t.thead(style="display:none"):
            with t.tr(style="text-align: right;"):
                t.th("info")
                t.th("data")
        with t.tbody():
            for doc in documents:
                _document_item(libname=libname,
                               libfolder=libfolder,
                               doc=doc)
        t.script(script)
    return result


def _index(pretitle: str,
           libname: str,
           libfolder: str,
           query: str,
           documents: List[papis.document.Document]) -> t.html_tag:
    with t.html() as result:
        _header(pretitle)
        with t.body():
            _navbar(libname=libname)
            with _container():
                with t.h1("Papis library: "):
                    t.code(libname)
                    _clear_cache(libname)
                with t.h3():
                    with t.form(method="GET",
                                action=("/library/{libname}/query"
                                        .format(libname=libname))):
                        t.input_(cls="form-control",
                                 type="text",
                                 name="q",
                                 value=(""
                                        if query == QUERY_PLACEHOLDER
                                        else query),
                                 placeholder=query)
                # Add a couple of friendlier messages
                if not documents:
                    if query == QUERY_PLACEHOLDER:
                        with t.h4(cls="alert alert-success"):
                            _icon("search")
                            t.span("Place your query")
                    else:
                        with t.h4(cls="alert alert-warning"):
                            _icon("database")
                            t.span("Ups! I didn't find {}".format(query))
                else:
                    _jquery_table(libname=libname,
                                  libfolder=libfolder,
                                  documents=documents)
    return result


def _tag(tag: str, libname: str) -> t.html_tag:
    return t.a(tag,
               cls="badge bg-dark papis-tag",
               href=("/library/{libname}/query?q=tags:{0}"
                     .format(tag, libname=libname)))


def _tags(pretitle: str, libname: str, tags: Dict[str, int]) -> t.html_tag:
    with t.html() as result:
        _header(pretitle)
        with t.body():
            _navbar(libname=libname)
            with _container():
                with t.h1("TAGS"):
                    with t.a(href="/library/{}/tags/refresh".format(libname)):
                        _icon("refresh")
                with _container():
                    for tag in sorted(tags,
                                      key=lambda k: tags[k],
                                      reverse=True):
                        _tag(tag=tag, libname=libname)
    return result


def _libraries(libname: str) -> t.html_tag:
    with t.html() as result:
        _header("Libraries")
        with t.body():
            _navbar(libname=libname)
            with _container():
                t.h1("Library selection")
                with t.ol(cls="list-group"):
                    libs = papis.api.get_libraries()
                    for lib in libs:
                        with t.a(href="/library/{}".format(lib)):
                            t.attr(cls="list-group-item "
                                   "list-group-item-action")
                            _icon("book")
                            t.span(lib)
    return result


def _doc_files_icons(files: List[str],
                     libname: str,
                     libfolder: str) -> t.html_tag:
    with t.div() as result:
        for _f in files:
            with t.a():
                t.attr(cls=PAPIS_FILE_ICON_CLASS)
                t.attr(data_bs_toggle="tooltip")
                t.attr(data_bs_placement="bottom")
                t.attr(style="font-size: 1.5em")
                t.attr(title=os.path.basename(_f))
                t.attr(href="/library/{libname}/file/{0}"
                       .format(_f.replace(libfolder + "/", ""),
                               libname=libname))
                _icon("file-pdf" if _f.endswith("pdf") else "file")
    return result


def _document_view(libname: str, doc: papis.document.Document) -> t.html_tag:
    """
    View of a single document to edit the information of the yaml file,
    and maybe in the future to update the information.
    """
    input_types = {
        # "string": default
        "textarea": ["abstract"],
        "number": ["year", "volume", "month", "issue"],
    }
    with t.html() as result:
        _header(doc["title"])
        with t.body():
            _navbar(libname=libname)
            with _container():
                t.h3(doc["title"])
                t.h5("{:.80}, {}".format(doc["author"], doc["year"]),
                     style="font-style: italic")
                with _container():
                    # urls block
                    with _flex("between"):
                        with _flex("begin"):
                            t.a("@{}".format(doc["ref"]),
                                href="#",
                                cls="btn btn-outline-success")
                        with _flex("center"):
                            t.button("Submit to edit",
                                     form="edit-form",
                                     cls="btn btn-success",
                                     type="submit")
                        with _flex("end"):
                            with t.div(cls="btn-group",
                                       role="group",
                                       aria_label=("List of external "
                                                   "links to the document")):
                                if "doi" in doc:
                                    with t.a(href=("https://doi.org/{}"
                                                   .format(doc["doi"])),
                                             target="_blank",
                                             cls="btn btn-outline-danger"):
                                        _icon("check-circle")
                                        t.span("doi")
                                if "url" in doc:
                                    with t.a(href="{}".format(doc["url"]),
                                             target="_blank",
                                             cls="btn btn-outline-danger"):
                                        _icon("external-link")
                                        t.span("url")
                                with t.a(href=("https://duckduckgo.com/?q={}"
                                               .format(urllib
                                                       .parse
                                                       .quote(papis.document
                                                              .describe(doc),
                                                              safe=""))),
                                         target="_blank",
                                         cls="btn btn-outline-danger"):
                                    _icon("globe", namespace="fa-solid")
                                    t.span("ddg")

                    t.br()

                    # the said form
                    with t.form(method="POST",
                                id="edit-form",
                                action=("/library/{libname}/"
                                        "document/ref:{doc[ref]}"
                                        .format(doc=doc, libname=libname))):
                        for key, val in doc.items():
                            if isinstance(val, (list, dict)):
                                continue
                            with t.div(cls="input-group mb-3"):
                                t.label(key,
                                        cls="input-group-text",
                                        _for=key)
                                if key in input_types["textarea"]:
                                    t.textarea(val,
                                               cls="form-control",
                                               placeholder=str(val),
                                               name=key,
                                               style="height: 100px")
                                elif key in input_types["number"]:
                                    t.input_(value=val,
                                             cls="form-control",
                                             name=key,
                                             placeholder=str(val),
                                             type="number")
                                else:
                                    t.input_(value=val,
                                             cls="form-control",
                                             name=key,
                                             placeholder=str(val),
                                             type="text")

                                with t.label(cls="input-group-text",
                                             _for=key):
                                    _icon("close")
    return result


def ensure_tags_list(tags: Union[str, List[str]]) -> List[str]:
    """
    Ensure getting a list of tags to render them.
    """
    if isinstance(tags, list):
        return tags
    return TAGS_SPLIT_RX.split(tags)


def _document_item(libname: str,
                   libfolder: str,
                   doc: papis.document.Document) -> t.html_tag:

    doc_link = ("/library/{libname}/document/ref:{ref}"
                .format(ref=doc["ref"],
                        libname=libname))

    with t.tr() as result:
        with t.td():

            with t.div(cls="ms-2 me-auto"):
                with t.div(cls="fw-bold"):
                    with t.a(href=doc_link):
                        _icon("arrow-right")
                    t.span(doc["title"])
                t.span(doc["author"])
                t.br()
                if doc.has("journal"):
                    _icon("book-open")
                    t.span(doc["journal"])
                    t.br()

                if doc.has("files"):
                    _doc_files_icons(files=doc.get_files(),
                                     libname=libname,
                                     libfolder=libfolder)

                if doc.has("citations"):
                    citations_id = "citatios{}".format(id(doc))
                    with t.a():
                        t.attr(data_bs_toggle="modal",
                               cls="",
                               aria_expanded="false",
                               href="#" + citations_id,
                               role="button")
                        _icon("list")
                        t.span("citations")

                    def body() -> t.html_tag:
                        with t.ul(cls="list-group") as result:
                            for cit in doc["citations"]:
                                with t.li():
                                    t.attr(cls=("list-group-item"))
                                    for key in ("title",
                                                "author",
                                                "year",
                                                "publisher"):
                                        if key in cit:
                                            t.span(cit[key])
                                    if "doi" in cit:
                                        t.a("doi",
                                            target="_blank",
                                            href=("https://doi.org/{}"
                                                  .format(cit["doi"])))
                                    if "url" in cit:
                                        t.a("url",
                                            target="_blank",
                                            href=doc["url"])
                        return result

                    _modal(body=body, id=citations_id)

        with t.td():
            if doc.has("tags"):
                with t.span(cls="papis-tags"):
                    _icon("hashtag")
                    for tag in ensure_tags_list(doc["tags"]):
                        _tag(tag=tag, libname=libname)
                    t.br()

            if doc.has("year"):
                t.span(doc["year"], cls="badge bg-primary papis-year")
            else:
                t.span("????", cls="badge bg-danger papis-year")

            if doc.has("ref"):
                with t.a(cls="badge bg-success", href=doc_link):
                    _icon("at")
                    t.span(doc["ref"])

            with t.ul(cls="list-group list-group-horizontal"):

                def url_link(title: str, href: str) -> t.html_tag:
                    return t.a(title,
                               href=href,
                               cls="list-group-item list-group-item-action",
                               target="_blank")

                if doc.has("url"):
                    url_link("url", doc["url"])
                if doc.has("doi"):
                    quoted_doi = (urllib
                                  .parse
                                  .quote(":" + doc["doi"], safe=""))
                    url_link("doi",
                             "https://doi.org/{}".format(doc["doi"]))
                    url_link("ads",
                             "https://ui.adsabs.harvard.edu/search/q=doi{}"
                             .format(quoted_doi))
                else:
                    quoted_title = urllib.parse.quote(doc["title"])
                    url_link("xref",
                             "https://search.crossref.org/?q={}&from_ui=yes"
                             .format(quoted_title))
                    url_link("ads",
                             "https://ui.adsabs.harvard.edu/search/q=title:{}"
                             .format(quoted_title))

    return result


AnyFn = Callable[..., Any]


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
    The main request handler of the papis web application.
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
        cleaned_query = urllib.parse.unquote_plus(query)
        docs = papis.api.get_documents_in_lib(libname, cleaned_query)
        self.page_main(libname, docs, cleaned_query)

    def page_main(self,
                  libname: Optional[str] = None,
                  docs: Optional[List[papis.document.Document]] = None,
                  query: Optional[str] = None) -> None:
        if docs is None:
            docs = []

        self.send_response(200)
        self.send_header_html()
        self.end_headers()
        libname = libname or papis.api.get_lib_name()
        if len(docs) == 0:
            if papis.config.getboolean("serve-empty-query-get-all-documents"):
                docs = papis.api.get_all_documents_in_lib(libname)
        libfolder = papis.config.get_lib_from_name(libname).paths[0]
        page = _index(documents=docs,
                      libname=libname,
                      libfolder=libfolder,
                      pretitle=query or "HOME",
                      query=query or QUERY_PLACEHOLDER)
        self.wfile.write(bytes(str(page), "utf-8"))
        self.wfile.flush()

    @ok_html
    @redirecting("/library")
    def clear_cache(self, libname: str) -> None:
        db = papis.database.get(libname)
        db.clear()
        db.initialize()

    @ok_html
    def page_tags(self, libname: Optional[str] = None) -> None:
        global TAGS_LIST
        libname = libname or papis.api.get_lib_name()
        docs = papis.api.get_all_documents_in_lib(libname)
        tags_of_tags = [tag
                        for d in docs
                        for tag in ensure_tags_list(d["tags"])]
        if TAGS_LIST.get(libname) is None:
            TAGS_LIST[libname] = collections.defaultdict(int)
            for tag in tags_of_tags:
                TAGS_LIST[libname][tag] += 1  # type: ignore
        page = _tags(libname=libname,
                     pretitle="TAGS",
                     tags=TAGS_LIST[libname] or {})
        self.wfile.write(bytes(str(page), "utf-8"))
        self.wfile.flush()

    @ok_html
    def page_tags_refresh(self, libname: Optional[str] = None) -> None:
        libname = libname or papis.api.get_lib_name()
        TAGS_LIST[libname] = None
        self.redirect("/library/{}/tags".format(libname))

    @ok_html
    def page_libraries(self) -> None:
        libname = papis.api.get_lib_name()
        page = _libraries(libname=libname)
        self.wfile.write(bytes(str(page), "utf-8"))
        self.wfile.flush()

    @ok_html
    def page_document(self, libname: str, ref: str) -> None:
        docs = papis.api.get_documents_in_lib(libname, ref)
        if len(docs) > 1:
            raise Exception("More than one document matched ref '{}'".format(ref))
        if not docs:
            raise Exception("No document found with ref '{}'".format(ref))

        page = _document_view(libname=libname, doc=docs[0])
        self.wfile.write(bytes(str(page), "utf-8"))
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
        self.send_header_html()
        self.send_header("Location", url)
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
        path = os.path.join(libfolder, localpath)
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

    def do_ROUTES(self,                     # noqa: N802
                  routes: List[Tuple[str, Any]]) -> None:
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
        db = papis.database.get(libname)
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={"REQUEST_METHOD": "POST"}
        )
        docs = db.query_dict(dict(ref=ref))
        if not docs:
            raise Exception("Document with ref %s not "
                            "found in the database" % ref)
        doc = docs[0]
        result = {}
        for key in form:
            result[key] = form.getvalue(key)
        papis.commands.update.run(doc, result, git=USE_GIT)
        back_url = self.headers.get("Referer", "/library")
        self.redirect(back_url)

    def do_POST(self) -> None:              # noqa: N802
        routes = [
            ("^/library/?([^/]+)?/document/ref:(.*)$",
                self.update_page_document),
        ]
        self.do_ROUTES(routes)

    def do_GET(self) -> None:               # noqa: N802
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
            ("^/library/([^/]+)/tags/refresh$",
                self.page_tags_refresh),
            ("^/library/([^/]+)/file/(.+)$",
                self.send_local_document_file),
            ("^/library/([^/]+)/clear_cache$",
                self.clear_cache),
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
    logger.info("starting server in address http://%s:%s",
                address or "localhost",
                port)
    logger.info("press Ctrl-C to exit")
    logger.info("THIS COMMAND IS EXPERIMENTAL, "
                "expect bugs, feedback appreciated")
    httpd = http.server.HTTPServer(server_address, PapisRequestHandler)
    httpd.serve_forever()
