"""
Creates the libraries view.
"""
from __future__ import annotations

import dominate.tags as t

import papis.web.header
import papis.web.html as wh
import papis.web.navbar


def html(libname: str) -> t.html_tag:
    from papis.api import get_libraries

    with papis.web.header.main_html_document("Libraries") as result, result.body:
        papis.web.navbar.navbar(libname=libname)
        with wh.container():
            t.h1("Library selection")
            with t.ol(cls="list-group"):
                libs = get_libraries()
                for lib in libs:
                    with t.a(href=f"/library/{lib}"):
                        t.attr(cls="list-group-item "
                               "list-group-item-action")
                        wh.icon("book")
                        t.span(lib)
    return result
