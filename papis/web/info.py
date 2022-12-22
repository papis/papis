import random
from typing import Any

import dominate.tags as t
import dominate.util as tu

import papis.document

import papis.web.paths as wp
import papis.web.html as wh
import papis.web.ace


def textarea(content: str, onsubmit_name: str, **kwargs: Any) -> str:
    """
    Creates a textareaand a p html element that seamlessly
    work on submission of the enclosing form.

    The names of the ids and the submission functions are
    safe-ish.
    """
    _random = random.randint(0, 10000)
    _yaml_input_id = "textarea-info-yaml-id_{}".format(_random)
    _yaml_id = "info-yaml-id_{}".format(_random)
    editor_name = "_editor_yaml_{}".format(_random)
    onsubmit_body = papis.web.ace.make_onsubmit_function(onsubmit_name,
                                                         editor_name,
                                                         _yaml_input_id)
    t.textarea(type="text",
               id=_yaml_input_id,
               style="display: none;",
               value=content,
               **kwargs)

    t.p(content,
        id=_yaml_id,
        style="min-height: 500px",
        cls="w-100")
    _script = """
    let {editor} = ace.edit("{}");
    {editor}.session.setMode("ace/mode/yaml");
    {}
    """.format(_yaml_id, onsubmit_body, editor=editor_name)
    t.script(tu.raw(_script),
             charset="utf-8",
             type="text/javascript")

    return editor_name


def widget(doc: papis.document.Document, libname: str) -> None:
    _yaml_content = ""
    onsubmit_name = "update_info_text_form"

    with open(doc.get_info_file()) as f:
        _yaml_content = f.read()

    with wh.flex("center"):
        with t.form(method="POST",
                    onsubmit="{}()".format(onsubmit_name),
                    cls="p-3 w-100",
                    action=wp.update_info(libname, doc)):

            textarea(content=_yaml_content,
                     onsubmit_name=onsubmit_name,
                     name="value")
            with t.button(cls="btn btn-success", type="submit"):
                wh.icon_span("check", "overwrite info.yaml")
