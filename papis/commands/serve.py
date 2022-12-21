import re
import os
import json
import logging
import http.server
import urllib.parse
from typing import Any, List, Optional, Tuple, Callable, Dict
import functools
import cgi
import collections
import tempfile

import click
import dominate.tags as t
import dominate.util as tu

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

import papis.web.header
import papis.web.navbar
import papis.web.paths as wp
import papis.web.html as wh

# widgets
import papis.web.timeline
import papis.web.notes
import papis.web.info

# views
import papis.web.libraries
import papis.web.tags


logger = logging.getLogger("papis:server")

USE_GIT = False  # type: bool
TAGS_LIST = {}  # type: Dict[str, Optional[Dict[str, int]]]
QUERY_PLACEHOLDER = "insert query..."
PAPIS_FILE_ICON_CLASS = "papis-file-icon"


def _clear_cache(libname: str) -> None:
    with t.a(href="/library/{libname}/clear_cache".format(libname=libname)):
        t.i(cls=wh.fa("refresh"),
            data_bs_toggle="tooltip",
            title="Clear Cache")


def _jquery_table(libname: str,
                  libfolder: str,
                  documents: List[papis.document.Document]) -> t.html_tag:
    script = """
    $(document).ready(function(){
        $('#pub_table').DataTable({
            'bSort': false,
            'language': {
                'info': "Page _PAGE_ of _PAGES_",
                'search': 'Filter results:'
            }
        });
    });
    """
    with t.table(border="1",
                 style="width: '100%'",
                 cls="display", id="pub_table") as result:
        with t.thead(style="display:none"):
            with t.tr(style="text-align: right;"):
                t.th("info")
                t.th("data")
        with t.tbody():
            for doc in documents:
                _document_item(libname=libname,
                               libfolder=libfolder,
                               doc=doc)
        t.script(tu.raw(script))
    return result


def _index(pretitle: str,
           libname: str,
           libfolder: str,
           query: str,
           documents: List[papis.document.Document]) -> t.html_tag:
    with papis.web.header.main_html_document(pretitle) as result:
        with result.body:
            papis.web.navbar.navbar(libname=libname)
            with wh.container():
                with t.h1("Papis library: "):
                    t.code(libname)
                    _clear_cache(libname)
                with t.h3():
                    with t.form(method="GET",
                                action=wp.query_path(libname)):
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
                        with wh.alert(t.h4, "success"):
                            wh.icon_span("search", "Place your query")
                    else:
                        with wh.alert(t.h4, "warning"):
                            wh.icon_span("database",
                                         "Ups! I didn't find for '{}'", query)
                else:
                    if papis.config.getboolean("serve-enable-timeline"):
                        if (len(documents)
                            < (papis.config.getint("serve-timeline-max")
                               or 500)):
                            papis.web.timeline.widget(documents,
                                                      libname,
                                                      "main-index-timeline")
                        else:
                            with wh.alert(t.p, "warning"):
                                wh.icon_span("warning",
                                             "Too many documents ({}) for "
                                             "a timeline to be useful",
                                             len(documents))
                    _jquery_table(libname=libname,
                                  libfolder=libfolder,
                                  documents=documents)
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
                t.attr(href=wp.file_server_path(_f, libfolder, libname))
                wh.file_icon(_f)
    return result


def _document_view_main_form(libname: str,
                             doc: papis.document.Document) -> t.html_tag:
    input_types = {
        # "string": default
        "textarea": ["abstract"],
        "number": ["year", "volume", "month", "issue"],
    }
    with t.div(cls="") as result:
        # urls block
        with wh.flex("between"):
            with wh.flex("begin"):
                t.a("@{}".format(doc["ref"]),
                    href="#",
                    cls="btn btn-outline-success")
            with wh.flex("center"):
                t.button("Submit to edit",
                         form="edit-form",
                         cls="btn btn-success",
                         type="submit")
            with wh.flex("end"):
                _links_btn_group(doc, small=False)

        t.br()

        # the said form
        with t.form(method="POST",
                    id="edit-form",
                    action=wp.doc_server_path(libname, doc)):
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
                        wh.icon("close")
            # end for

            with t.div(cls="input-group mb-3"):
                t.input_(placeholder="New key",
                         name="newkey-name",
                         value="",
                         cls="input-group-text",
                         _for="newkey-value")
                t.input_(value="",
                         cls="form-control",
                         name="newkey-value",
                         placeholder="New value",
                         type="text")
                with t.button(cls="input-group-text bg-success",
                              form="edit-form",
                              type="submit"):
                    wh.icon("plus")

    return result


def _render_citations(doc: papis.document.Document,
                      libname: str,
                      libfolder: str,
                      timeline_id: str,
                      fetch_path: Callable[[str, Dict[str, Any]], str],
                      checker: Callable[[papis.document.Document], bool],
                      getter: Callable[[papis.document.Document],
                                       papis.citations.Citations],
                      ads_fmt: str) -> None:

    with t.form(action=fetch_path(libname, doc),
                method="POST"):
        with t.div(cls="btn-group", role="group"):
            with t.button(cls="btn btn-success",
                          type="submit"):
                wh.icon_span("cloud-bolt", "Fetch citations")
            if doc.has("doi"):
                quoted_doi = urllib.parse.quote(doc["doi"], safe="")
                with t.a(cls="btn btn-primary",
                         target="_blank",
                         href=ads_fmt.format(doi=quoted_doi)):
                    wh.icon_span("globe", "ads")

    if checker(doc):
        citations = getter(doc)
        if papis.config.getboolean("serve-enable-timeline"):
            papis.web.timeline.widget(citations, libname, timeline_id)
        with t.ol(cls="list-group"):
            with t.li(cls="list-group-item"):
                for cit in citations:
                    _document_item(libname,
                                   libfolder,
                                   papis.document.from_data(cit))
    else:
        if doc.has("doi"):
            quoted_doi = urllib.parse.quote(doc["doi"], safe="")
            ads = ads_fmt.format(doi=quoted_doi)
            t.a("Provided by ads", href=ads)
            t.iframe(src=ads,
                     width="100%",
                     height="500",
                     style="width: '100%'")
        else:
            with wh.alert(t.h3, "danger"):
                wh.icon_span("error", "No citations available")


def _document_view(libname: str, doc: papis.document.Document) -> t.html_tag:
    """
    View of a single document to edit the information of the yaml file,
    and maybe in the future to update the information.
    """
    checks = papis.commands.doctor.registered_checks_names()
    errors = papis.commands.doctor.run(doc, checks)
    libfolder = papis.config.get_lib_from_name(libname).paths[0]

    with papis.web.header.main_html_document(doc["title"]) as result:
        with result.body:
            _click_tab_selector_link_in_url()
            papis.web.navbar.navbar(libname=libname)
            with wh.container():
                t.h3(doc["title"])
                t.h5("{:.80}, {}".format(doc["author"], doc["year"]),
                     style="font-style: italic")
                tags = doc["tags"]
                with wh.flex("between"):
                    if tags:
                        papis.web.tags.tags_list_div(tags, libname)
                    for fpath in doc.get_files():
                        with t.a(href=wp.file_server_path(fpath,
                                                          libfolder,
                                                          libname)):
                            wh.file_icon(fpath)
                for error in errors:
                    with wh.alert(t.div, "danger"):
                        wh.icon_span("stethoscope", error.msg)

                with t.ul(cls="nav nav-tabs"):

                    def _tab_element(content: Callable[..., t.html_tag],
                                     args: List[Any],
                                     href: str,
                                     active: bool = False) -> t.html_tag:
                        with t.li(cls="active nav-item") as result:
                            with t.a(cls="nav-link" + (" active"
                                                       if active
                                                       else ""),
                                     aria_current="page",
                                     id="selector-" + href.replace("#", ""),
                                     href=href,
                                     data_bs_toggle="tab"):
                                content(*args)
                        return result

                    _tab_element(t.span,
                                 ["Form"],
                                 "#main-form-tab", active=True)
                    _tab_element(wh.icon_span,
                                 ["circle-info", "info.yaml"],
                                 "#yaml-form-tab")
                    _tab_element(t.span, ["Bibtex"], "#bibtex-form-tab")
                    for i, fpath in enumerate(doc.get_files()):
                        _tab_element(wh.file_icon,
                                     [fpath],
                                     "#file-tab-{}".format(i))
                    _tab_element(t.span, ["Citations"], "#citations-tab")
                    _tab_element(t.span, ["Cited by"], "#cited-by-tab")
                    _tab_element(wh.icon_span, ["note", "Notes"],
                                 "#notes-tab")

                t.br()

                with t.div(cls="tab-content"):
                    with t.div(id="main-form-tab",
                               role="tabpanel",
                               aria_labelledby="main-form",
                               cls="tab-pane fade show active"):
                        _document_view_main_form(libname, doc)

                    with t.div(id="yaml-form-tab",
                               role="tabpanel",
                               aria_labelledby="yaml-form",
                               cls="tab-pane fade"):
                        papis.web.info.widget(doc, libname)

                    with t.div(id="bibtex-form-tab",
                               role="tabpanel",
                               aria_labelledby="bibtex-form",
                               cls="tab-pane fade"):
                        _bibtex_id = "bibtex-source"
                        t.div(papis.bibtex.to_bibtex(doc),
                              id=_bibtex_id,
                              width="100%",
                              height=100,
                              style="min-height: 500px",
                              cls="form-control")
                        _script = """
                            let bib_editor = ace.edit("{}");
                            bib_editor.session.setMode("ace/mode/bibtex");
                        """.format(_bibtex_id)
                        t.script(tu.raw(_script),
                                 charset="utf-8",
                                 type="text/javascript")

                    with t.div(id="notes-tab",
                               role="tabpanel",
                               aria_labelledby="notes-form",
                               cls="tab-pane fade"):
                        papis.web.notes.widget(libname, doc)

                    for i, fpath in enumerate(doc.get_files()):
                        if not fpath.endswith("pdf"):
                            continue
                        _unquoted_file_path = wp.file_server_path(fpath,
                                                                  libfolder,
                                                                  libname)
                        _file_path = urllib.parse.quote(_unquoted_file_path,
                                                        safe="")
                        viewer_path = ("/static/pdfjs/web/viewer.html?file={}"
                                       .format(_file_path))

                        with t.div(id="file-tab-{}".format(i),
                                   role="tabpanel",
                                   aria_labelledby="bibtex-form",
                                   cls="tab-pane fade"):

                            with wh.flex("center"):
                                with t.div(cls="btn-group", role="group"):
                                    with t.a(href=viewer_path,
                                             cls="btn btn-outline-success",
                                             target="_blank"):
                                        wh.icon_span("square-arrow-up-right",
                                                     "Open in new window")
                                    with t.a(href=_unquoted_file_path,
                                             cls="btn btn-outline-success",
                                             target="_blank"):
                                        wh.icon_span("download", "Download")

                            t.iframe(src=viewer_path,
                                     style="resize: vertical",
                                     width="100%",
                                     height="800")

                    with t.div(id="citations-tab",
                               role="tabpanel",
                               aria_labelledby="citations-tab",
                               cls="tab-pane fade"):
                        _render_citations(
                            doc,
                            libname,
                            libfolder,
                            timeline_id="main-citations-timeline",
                            fetch_path=wp.fetch_citations_server_path,
                            checker=papis.citations.has_citations,
                            getter=papis.citations.get_citations,
                            ads_fmt=("https://ui.adsabs.harvard.edu/abs/"
                                     "{doi}/references"))

                    with t.div(id="cited-by-tab",
                               role="tabpanel",
                               aria_labelledby="cited-by-tab",
                               cls="tab-pane fade"):
                        _render_citations(
                            doc,
                            libname,
                            libfolder,
                            timeline_id="main-cited-by-timeline",
                            fetch_path=wp.fetch_cited_by_server_path,
                            checker=papis.citations.has_cited_by,
                            getter=papis.citations.get_cited_by,
                            ads_fmt=("https://ui.adsabs.harvard.edu/abs/"
                                     "{doi}/citations"))

    return result


def _click_tab_selector_link_in_url() -> None:
    t.script(tu.raw("""
    window.addEventListener('load', () => {
        try {
            let url = window.location.href.split('#').pop();
            document.querySelector('#selector-'+url).click();
        } catch {}
    });
    """))


def _links_btn_group(doc: papis.document.Document, small: bool = True) -> None:
    with t.div(cls="btn-group", role="group"):

        def url_link(icon: str, title: str, href: str) -> None:
            with t.a(href=href,
                     cls="btn btn-outline-primary" + (" btn-sm"
                                                      if small
                                                      else ""),
                     target="_blank"):
                wh.icon_span(icon, title)

        if doc.has("url"):
            url_link("external-link", "url", doc["url"])
        if doc.has("doi"):
            quoted_doi = urllib.parse.quote(doc["doi"], safe="")
            url_link("check-circle", "doi",
                     "https://doi.org/{}".format(doc["doi"]))
            url_link("database", "ads",
                     "https://ui.adsabs.harvard.edu/abs/{}"
                     .format(quoted_doi))
            if not doc.has("files"):
                url_link("lock-open", "unp",
                         "https://unpaywall.org/{}".format(doc["doi"]))
        else:
            quoted_title = urllib.parse.quote(doc["title"])
            url_link("crosshairs", "xref",
                     "https://search.crossref.org/?q={}&from_ui=yes"
                     .format(quoted_title))
            url_link("database", "ads",
                     "https://ui.adsabs.harvard.edu/search/q=title:{}"
                     .format(quoted_title))

        url_link("globe", "ddg",
                 "https://duckduckgo.com/?q={}"
                 .format(urllib.parse.quote(papis.document.describe(doc),
                                            safe="")))


def _document_item(libname: str,
                   libfolder: str,
                   doc: papis.document.Document) -> t.html_tag:

    doc_link = wp.doc_server_path(libname, doc)

    with t.tr() as result:
        with t.td():

            with t.div(cls="ms-2 me-auto"):
                with t.div(cls="fw-bold"):
                    with t.a(href=doc_link):
                        wh.icon("arrow-right")
                    t.span(doc["title"])
                t.span(doc["author"])
                t.br()
                if doc.has("journal"):
                    wh.icon("book-open")
                    t.span(doc["journal"])
                    t.br()

                if doc.has("files"):
                    _doc_files_icons(files=doc.get_files(),
                                     libname=libname,
                                     libfolder=libfolder)
        with t.td():
            if doc.has("tags"):
                papis.web.tags.tags_list_div(doc["tags"], libname)
                t.br()

            if doc.has("year"):
                t.span(doc["year"], cls="badge bg-primary papis-year")
            else:
                t.span("!!!!", cls="badge bg-danger papis-year")
            t.br()
            if doc.has("ref"):
                with t.a(cls="badge bg-success", href=doc_link):
                    wh.icon("at")
                    t.span(doc["ref"])
            t.br()
            _links_btn_group(doc)

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
        self._handle_lib(libname)
        cleaned_query = urllib.parse.unquote_plus(query)
        docs = papis.api.get_documents_in_lib(libname, cleaned_query)
        self.page_main(libname, docs, cleaned_query)

    def page_main(self,
                  libname: Optional[str] = None,
                  docs: Optional[List[papis.document.Document]] = None,
                  query: Optional[str] = None) -> None:
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
        self._handle_lib(libname)
        db = papis.database.get(libname)
        db.clear()
        db.initialize()

    @ok_html
    def page_tags(self, libname: Optional[str] = None) -> None:
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
                TAGS_LIST[libname][tag] += 1  # type: ignore

        page = papis.web.tags.html(libname=libname,
                                   pretitle="TAGS",
                                   tags=TAGS_LIST[libname] or {})

        self.wfile.write(bytes(str(page), "utf-8"))
        self.wfile.flush()

    @ok_html
    def page_tags_refresh(self, libname: Optional[str] = None) -> None:
        libname = libname or papis.api.get_lib_name()
        self._handle_lib(libname)
        TAGS_LIST[libname] = None
        self.redirect("/library/{}/tags".format(libname))

    @ok_html
    def page_libraries(self) -> None:
        libname = papis.api.get_lib_name()
        page = papis.web.libraries.html(libname=libname)
        self.wfile.write(bytes(str(page), "utf-8"))
        self.wfile.flush()

    @ok_html
    def page_document(self, libname: str, papis_id: str) -> None:
        doc = self._get_document(libname, papis_id)
        page = _document_view(libname=libname, doc=doc)
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
        self._send_json({"name": lib.name, "paths": lib.paths})

    def get_all_documents(self, libname: str) -> None:
        self._handle_lib(libname)
        docs = papis.api.get_all_documents_in_lib(libname)
        self.serve_documents(docs)

    def get_query(self, libname: str, query: str) -> None:
        self._handle_lib(libname)
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
            raise Exception("File {} does not exist".format(path))

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
                                  "Server path {0} not understood"
                                  .format(self.path))

    def _handle_lib(self, libname: str) -> None:
        papis.api.set_lib_from_name(libname)

    def _get_document(self,
                      libname: str,
                      papis_id: str) -> papis.document.Document:
        self._handle_lib(libname)
        db = papis.database.get(libname)
        doc = db.find_by_id(papis_id)
        if not doc:
            raise Exception("Document with ref %s not "
                            "found in the database" % papis_id)
        return doc

    def _get_form(self, method: str = "POST") -> cgi.FieldStorage:
        return cgi.FieldStorage(fp=self.rfile,
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
        yaml_to_data function. If it is succesfull it supposes
        it is a correct yaml, it overwrites the old yaml
        and updates the database and the document with it.
        """
        doc = self._get_document(libname, papis_id)
        form = self._get_form("POST")
        new_info = form.getvalue("value")
        info_path = doc.get_info_file()

        logger.info("checking syntax of the yaml")
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as fdr:
            fdr.write(new_info)
        try:
            papis.yaml.yaml_to_data(fdr.name, raise_exception=True)
        except ValueError as e:
            self._send_json_error(404, "Error in yaml: {}".format(e))
            os.unlink(fdr.name)
            return
        else:
            os.unlink(fdr.name)
            logger.info("info text seems ok")
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
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "static",
                            urllib.parse.unquote_plus(static_path))
        if os.path.exists(path):
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
        else:
            raise Exception("File {} does not exist".format(path))

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
            ("^/library/?([^/]+)?/query[?]q=(.*)$",
                self.page_query),
            ("^/library/?([^/]+)?/document/([a-z0-9]+)$",
                self.page_document),
            ("^/library/([^/]+)/tags$",
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
    logger.info("starting server in address http://%s:%s",
                address or "localhost",
                port)
    logger.info("press Ctrl-C to exit")
    logger.info("THIS COMMAND IS EXPERIMENTAL, "
                "expect bugs, feedback appreciated")
    httpd = http.server.HTTPServer(server_address, PapisRequestHandler)
    httpd.serve_forever()
