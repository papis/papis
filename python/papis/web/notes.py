from __future__ import annotations

import os
from typing import TYPE_CHECKING

import dominate.tags as t
import dominate.util as tu

import papis.web.ace
import papis.web.html as wh
import papis.web.paths as wp

if TYPE_CHECKING:
    from papis.document import Document


def widget(libname: str, doc: Document) -> None:
    notes_id = "notes-source"
    notes_input_id = "notes-input-source"
    notes_content = ""
    editor_name = "notes_editor"
    onsubmit_name = "update_notes_text_form"
    onsubmit_body = papis.web.ace.make_onsubmit_function(onsubmit_name,
                                                         editor_name,
                                                         notes_input_id)

    # TODO add org mode somehow and check extensions
    from papis.notes import has_notes, notes_path

    notes_extension = "markdown"
    if has_notes(doc):
        filepath = notes_path(doc)
        if os.path.exists(filepath):
            with open(filepath, encoding="utf-8") as fd:
                notes_content = fd.read()

    with wh.flex("center"):
        with t.form(method="POST",
                    cls="p-3",
                    onsubmit=f"{onsubmit_name}()",
                    action=wp.update_notes(libname, doc)):
            t.textarea(type="text",
                       id=notes_input_id,
                       style="display: none;",
                       name="value",
                       value=notes_content)
            with t.button(cls="btn btn-success", type="submit"):
                wh.icon_span("check", "update notes")

    t.p(notes_content,
        id=notes_id,
        width="100%",
        height=100,
        style="min-height: 500px")

    script = f"""
let {editor_name} = ace.edit("{notes_id}");
ace.require('ace/ext/settings_menu').init({editor_name});
ace.config.loadModule('ace/ext/keybinding_menu',
                        (module) =>  {{
                            module.init({editor_name});
                        }});
// {editor_name}.setKeyboardHandler('ace/keyboard/vim');
{editor_name}.session.setMode("ace/mode/{notes_extension}");

{onsubmit_body}
    """

    t.script(tu.raw(script),
             charset="utf-8",
             type="text/javascript")
