from typing import Any, Callable, Dict
import urllib.parse

import dominate.tags as t

import papis.document
import papis.citations

import papis.web.timeline
import papis.web.document
import papis.web.html as wh


def render(doc: papis.document.Document,
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
            if "doi" in doc:
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
                    papis.web.document.render(libname,
                                              libfolder,
                                              papis.document.from_data(cit))
    else:
        if "doi" in doc:
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
