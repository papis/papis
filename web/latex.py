import dominate.tags as t
import dominate.util as tu

import papis.config


def katex_header() -> t.html_tag:
    """
    Everything connected to Katex
    """
    t.link(rel="stylesheet",
           type="text/css",
           href=papis.config.getstring("serve-katex-css"))
    t.script(type="text/javascript",
             charset="utf8",
             defer=True,
             src=papis.config.getstring("serve-katex-js"))
    t.script(type="text/javascript",
             charset="utf8",
             defer=True,
             src=papis.config.getstring("serve-katex-auto-render-js"))
    katex_script = r"""
document.addEventListener('DOMContentLoaded', () => {
    renderMathInElement(document.body, {
        delimiters: [
            {left: "$$", right: "$$", display: true},
            {left: "$", right: "$", display: false},
            {left: "\\(", right: "\\)", display: false},
            {left: "\\begin{equation}", right: "\\end{equation}",
             display: true},
            {left: "\\begin{equation*}", right: "\\end{equation*}",
             display: true},
            {left: "\\begin{align}", right: "\\end{align}", display: true},
            {left: "\\begin{align*}", right: "\\end{align*}", display: true},
            {left: "\\begin{alignat}", right: "\\end{alignat}", display: true},
            {left: "\\begin{gather}", right: "\\end{gather}", display: true},
            {left: "\\begin{CD}", right: "\\end{CD}", display: true},
            {left: "\\[", right: "\\]", display: true}
        ],
    });
});

        """
    t.script(tu.raw(katex_script),
             charset="utf8",
             type="text/javascript")
