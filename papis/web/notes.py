import os

import dominate.tags as t
import dominate.util as tu

import papis.notes
import papis.document

import papis.web.paths as wp
import papis.web.html as wh
import papis.web.ace


def widget(libname: str, doc: papis.document.Document) -> None:
    _notes_id = "notes-source"
    _notes_input_id = "notes-input-source"
    _notes_content = ""
    editor_name = "notes_editor"
    onsubmit_name = "update_notes_text_form"
    onsubmit_body = papis.web.ace.make_onsubmit_function(onsubmit_name,
                                                         editor_name,
                                                         _notes_input_id)

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
                    onsubmit="{}()".format(onsubmit_name),
                    action=wp.update_notes(libname, doc)):
            t.textarea(type="text",
                       id=_notes_input_id,
                       style="display: none;",
                       name="value",
                       value=_notes_content)
            with t.button(cls="btn btn-success", type="submit"):
                wh.icon_span("check", "update notes")

    t.p(_notes_content,
        id=_notes_id,
        width="100%",
        height=100,
        style="min-height: 500px")

    _script = """
let {editor} = ace.edit("{editor_id}");
ace.require('ace/ext/settings_menu').init({editor});
ace.config.loadModule('ace/ext/keybinding_menu',
                        (module) =>  {{
                            module.init({editor});
                        }});
// {editor}.setKeyboardHandler('ace/keyboard/vim');
{editor}.session.setMode("ace/mode/{ext}");

{onsubmit}
    """.format(onsubmit=onsubmit_body,
               editor=editor_name,
               ext=_notes_extension,
               editor_id=_notes_id)

    t.script(tu.raw(_script),
             charset="utf-8",
             type="text/javascript")
