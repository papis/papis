import os
import urllib.parse
from typing import List

import dominate.tags as t

import papis.document
import papis.web.tags
import papis.web.html as wh
import papis.web.paths as wp


def links(doc: papis.document.Document, small: bool = True) -> None:
    with t.div(cls="btn-group", role="group"):

        def url_link(icon: str, title: str, href: str) -> None:
            with t.a(href=href,
                     cls="btn btn-outline-primary" + (" btn-sm"
                                                      if small
                                                      else ""),
                     target="_blank"):
                wh.icon_span(icon, title)

        if "url" in doc:
            url_link("external-link", "url", doc["url"])
        if "doi" in doc:
            quoted_doi = urllib.parse.quote(doc["doi"], safe="")
            url_link("check-circle", "doi",
                     "https://doi.org/{}".format(doc["doi"]))
            url_link("database", "ads",
                     "https://ui.adsabs.harvard.edu/abs/{}"
                     .format(quoted_doi))
            if "files" not in doc:
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


def _doc_files_icons(files: List[str],
                     libname: str,
                     libfolder: str) -> t.html_tag:
    with t.div() as result:
        for _f in files:
            with t.a():
                t.attr(data_bs_toggle="tooltip")
                t.attr(data_bs_placement="bottom")
                t.attr(style="font-size: 1.5em")
                t.attr(title=os.path.basename(_f))
                t.attr(href=wp.file_server_path(_f, libfolder, libname))
                wh.file_icon(_f)
    return result


def render(libname: str,
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
                if "journal" in doc:
                    wh.icon("book-open")
                    t.span(doc["journal"])
                    t.br()

                if "files" in doc:
                    _doc_files_icons(files=doc.get_files(),
                                     libname=libname,
                                     libfolder=libfolder)
        with t.td():
            if "tags" in doc:
                papis.web.tags.tags_list_div(doc["tags"], libname)
                t.br()

            if "year" in doc:
                t.span(doc["year"], cls="badge bg-primary papis-year")
            else:
                t.span("!!!!", cls="badge bg-danger papis-year")
            t.br()
            if "ref" in doc:
                with t.a(cls="badge bg-success", href=doc_link):
                    wh.icon("at")
                    t.span(doc["ref"])
            t.br()
            links(doc)

    return result
