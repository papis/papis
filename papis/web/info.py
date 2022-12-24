import dominate.tags as t
import dominate.util as tu

import papis.document

import papis.web.paths as wp
import papis.web.html as wh
import papis.web.ace


def widget(doc: papis.document.Document, libname: str) -> None:
    _yaml_id = "info-yaml-source"
    _yaml_input_id = "info-yaml-textarea"
    _yaml_content = ""
    editor_name = "yaml_editor"
    onsubmit_name = "update_info_text_form"
    onsubmit_body = papis.web.ace.make_onsubmit_function(onsubmit_name,
                                                         editor_name,
                                                         _yaml_input_id)

    with open(doc.get_info_file()) as f:
        _yaml_content = f.read()

    with wh.flex("center"):
        with t.form(method="POST",
                    onsubmit="{}()".format(onsubmit_name),
                    cls="p-3",
                    action=wp.update_info(libname, doc)):
            t.textarea(type="text",
                       id=_yaml_input_id,
                       style="display: none;",
                       name="value",
                       value=_yaml_content)
            with t.button(cls="btn btn-success", type="submit"):
                wh.icon_span("check", "overwrite info.yaml")

    t.p(_yaml_content,
        id=_yaml_id,
        width="100%",
        height=100,
        style="min-height: 500px",
        cls="form-control")

    _script = """
    let {editor} = ace.edit("{}");
    {editor}.session.setMode("ace/mode/yaml");
    {}
    """.format(_yaml_id, onsubmit_body, editor=editor_name)

    t.script(tu.raw(_script),
             charset="utf-8",
             type="text/javascript")
