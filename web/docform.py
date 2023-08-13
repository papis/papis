import dominate.tags as t

import papis.document

import papis.web.document
import papis.web.html as wh
import papis.web.paths as wp


def html(libname: str,
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
                papis.web.document.links(doc, small=False)

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
