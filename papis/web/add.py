import dominate.tags as t

import papis.web.header
import papis.web.navbar
import papis.web.html as wh
import papis.web.paths as wp
import papis.web.info

URL_PLACEHOLDER = "http://www.nature.com/articles/Art376238a0"
DEFAULT_INFO = """\
##
## Add additional content to the yaml file like so
##
#tags: project-thesis organic-chemistry
#author: Alonzo Church
"""


def html(libname: str) -> t.html_tag:
    with papis.web.header.main_html_document("Add document") as result:
        with result.body:
            papis.web.navbar.navbar(libname=libname)
            with wh.container():

                t.h3("Add document")
                form_group_class = "mb-3 row"
                label_class = "col-sm-2 col-form-label"

                onsubmit_name = "update_info_text_form"

                with t.form(method="POST",
                            enctype="multipart/form-data",
                            onsubmit="{}()".format(onsubmit_name),
                            action=wp.add_path(libname)):
                    t.button("Add", type="submit", cls="btn btn-success")
                    with t.div(cls=form_group_class):
                        with t.label(for_="form-pdf", cls=label_class):
                            wh.icon_span("file-pdf", "PDF")
                        with t.div(cls="col-sm-10"):
                            t.input_(cls="form-control",
                                     name="pdf",
                                     type="file",
                                     id="form-pdf")
                    with t.div(cls=form_group_class):
                        t.label("doi",
                                for_="form-doi",
                                cls=label_class)
                        with t.div(cls="col-sm-10"):
                            t.input_(cls="form-control",
                                     name="doi",
                                     placeholder="10.1007/s10670-005-5814-y",
                                     type="text",
                                     id="form-doi")
                    with t.div(cls=form_group_class):
                        with t.label(for_="form-url",
                                     cls=label_class):
                            wh.icon_span("globe", "url")
                        with t.div(cls="col-sm-10"):
                            t.input_(cls="form-control",
                                     name="url",
                                     placeholder=URL_PLACEHOLDER,
                                     type="text",
                                     id="form-url")

                    with t.div(cls=form_group_class):
                        with t.label(for_="form-url",
                                     cls=label_class):
                            wh.icon_span("circle-info", "Info.yaml")
                        with t.div(cls="col-sm-10"):
                            papis.web.info.textarea(DEFAULT_INFO,
                                                    onsubmit_name=onsubmit_name,
                                                    name="info")

    return result
