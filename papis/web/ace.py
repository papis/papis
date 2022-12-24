"""
Module for helping ace.js editor functionality.
"""


def make_onsubmit_function(name: str, editor: str, content_id: str) -> str:
    return """
function {name}() {{
    let input = document.querySelector("#{_id}");
    input.value = {editor}.getValue();
}}
    """.format(name=name, editor=editor, _id=content_id)
