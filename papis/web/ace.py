"""
Module for helping ace.js editor functionality.
"""


def make_onsubmit_function(name: str, editor: str, content_id: str) -> str:
    return f"""
function {name}() {{
    let input = document.querySelector("#{content_id}");
    input.value = {editor}.getValue();
}}
    """
