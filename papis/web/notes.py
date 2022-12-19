import os

import dominate.tags as t
import dominate.util as tu

import papis.notes
import papis.document

import papis.web.paths as wp
import papis.web.html as wh


def widget(libname: str, doc: papis.document.Document) -> None:
    _notes_id = "notes-source"
    _notes_input_id = "notes-input-source"
    _notes_content = ""
    # TODO add org mode somehow and check extensions
    _notes_extension = "markdown"
    if papis.notes.has_notes(doc):
        filepath = papis.notes.notes_path(doc)
        if os.path.exists(filepath):
            with open(filepath) as _fd:
                _notes_content = _fd.read()

    with wh.flex("center"):
        with t.form(method="POST",
                    cls="p-3",
                    onsubmit="update_notes_text_form()",
                    action=wp.update_notes(libname, doc)):
            t.textarea(type="text",
                       id=_notes_input_id,
                       style="display: none;",
                       name="value",
                       value=_notes_content)
            with t.button(cls="btn btn-success"):
                wh.icon_span("check", "update notes")

    t.p(_notes_content,
        id=_notes_id,
        width="100%",
        height=100,
        style="min-height: 500px")

    _script = """
let notes_editor = ace.edit("{editor_id}");
ace.require('ace/ext/settings_menu').init(notes_editor);
ace.config.loadModule('ace/ext/keybinding_menu',
                        (module) =>  {{
                            module.init(notes_editor);
                        }});
notes_editor.setKeyboardHandler('ace/keyboard/vim');
notes_editor.session.setMode("ace/mode/{ext}");

function update_notes_text_form() {{
    let input = document.querySelector("#{}");
    input.value = notes_editor.getValue();
}}
    """.format(_notes_input_id,
               ext=_notes_extension,
               editor_id=_notes_id)
    t.script(tu.raw(_script),
             charset="utf-8",
             type="text/javascript")
