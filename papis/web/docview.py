from typing import Any, List, Callable

import dominate.tags as t
import dominate.util as tu

import papis.commands.doctor

import papis.web.paths as wp
import papis.web.html as wh
import papis.web.docform
import papis.web.header
import papis.web.notes
import papis.web.info
import papis.web.citations
import papis.web.pdfjs
import papis.web.djvujs
import papis.web.epubjs


def _click_tab_selector_link_in_url() -> None:
    t.script(tu.raw("""
    window.addEventListener('load', () => {
        try {
            let url = window.location.href.split('#').pop();
            document.querySelector('#selector-'+url).click();
        } catch {}
    });
    """))


def html(libname: str, doc: papis.document.Document) -> t.html_tag:
    """
    View of a single document to edit the information of the yaml file,
    and maybe in the future to update the information.
    """
    checks = papis.commands.doctor.registered_checks_names()
    errors = papis.commands.doctor.gather_errors([doc], checks)
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
                                 ["file-alt", "info.yaml"],
                                 "#yaml-form-tab")
                    _tab_element(t.span, ["Bibtex"], "#bibtex-form-tab")
                    for i, fpath in enumerate(doc.get_files()):
                        _tab_element(wh.file_icon,
                                     [fpath],
                                     f"#file-tab-{i}")
                    _tab_element(wh.icon_span,
                                 ["compress-alt", "Citations"],
                                 "#citations-tab")
                    _tab_element(wh.icon_span,
                                 ["expand-alt", "Cited by"],
                                 "#cited-by-tab")
                    _tab_element(wh.icon_span, ["file-edit", "Notes"],
                                 "#notes-tab")

                t.br()

                with t.div(cls="tab-content"):
                    with t.div(id="main-form-tab",
                               role="tabpanel",
                               aria_labelledby="main-form",
                               cls="tab-pane fade show active"):
                        papis.web.docform.html(libname, doc)

                    with t.div(id="yaml-form-tab",
                               role="tabpanel",
                               aria_labelledby="yaml-form",
                               cls="tab-pane fade"):
                        papis.web.info.widget(doc, libname)

                    with t.div(id="bibtex-form-tab",
                               role="tabpanel",
                               aria_labelledby="bibtex-form",
                               cls="tab-pane fade"):
                        bibtex_id = "bibtex-source"
                        t.div(papis.bibtex.to_bibtex(doc),
                              id=bibtex_id,
                              width="100%",
                              height=100,
                              style="min-height: 500px",
                              cls="form-control")
                        script = f"""
                            let bib_editor = ace.edit("{bibtex_id}");
                            bib_editor.session.setMode("ace/mode/bibtex");
                        """
                        t.script(tu.raw(script),
                                 charset="utf-8",
                                 type="text/javascript")

                    with t.div(id="notes-tab",
                               role="tabpanel",
                               aria_labelledby="notes-form",
                               cls="tab-pane fade"):
                        papis.web.notes.widget(libname, doc)

                    for i, fpath in enumerate(doc.get_files()):
                        unquoted_file_path = wp.file_server_path(fpath,
                                                                 libfolder,
                                                                 libname)

                        with t.div(id=f"file-tab-{i}",
                                   role="tabpanel",
                                   aria_labelledby="file-tab",
                                   cls="tab-pane fade"):

                            if fpath.endswith("pdf"):
                                papis.web.pdfjs.widget(unquoted_file_path)

                            if fpath.endswith("djvu"):
                                papis.web.djvujs.widget(unquoted_file_path)

                            if fpath.endswith("epub"):
                                papis.web.epubjs.widget(unquoted_file_path)

                            elif (fpath.endswith("png")
                                  or fpath.endswith("jpg")):
                                with t.div():
                                    t.img(src=unquoted_file_path)

                    with t.div(id="citations-tab",
                               role="tabpanel",
                               aria_labelledby="citations-tab",
                               cls="tab-pane fade"):
                        papis.web.citations.render(
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
                        papis.web.citations.render(
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
