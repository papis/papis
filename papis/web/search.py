from typing import List

import dominate.tags as t
import dominate.util as tu

import papis.document

import papis.web.header
import papis.web.navbar
import papis.web.paths as wp
import papis.web.html as wh

# widgets
import papis.web.document
import papis.web.timeline


QUERY_PLACEHOLDER = "insert query..."


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
                papis.web.document.render(libname=libname,
                                          libfolder=libfolder,
                                          doc=doc)
        t.script(tu.raw(script))
    return result


def html(pretitle: str,
         libname: str,
         libfolder: str,
         query: str,
         documents: List[papis.document.Document]) -> t.html_tag:
    """
    Page for querying the papis database and present the results.
    """
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
