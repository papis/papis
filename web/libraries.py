"""
Creates the libraries view.
"""
import dominate.tags as t

import papis.api

import papis.web.header
import papis.web.navbar
import papis.web.html as wh


def html(libname: str) -> t.html_tag:
    with papis.web.header.main_html_document("Libraries") as result:
        with result.body:
            papis.web.navbar.navbar(libname=libname)
            with wh.container():
                t.h1("Library selection")
                with t.ol(cls="list-group"):
                    libs = papis.api.get_libraries()
                    for lib in libs:
                        with t.a(href="/library/{}".format(lib)):
                            t.attr(cls="list-group-item "
                                   "list-group-item-action")
                            wh.icon("book")
                            t.span(lib)
    return result
