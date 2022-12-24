import dominate
import dominate.tags as t

import papis.config
import papis.web.latex


def header(pretitle: str) -> None:
    t.title("{} Papis web".format(pretitle))
    t.meta(name="apple-mobile-web-app-capable", content="yes")
    t.meta(charset="UTF-8")
    t.meta(name="apple-mobile-web-app-capable", content="yes")
    t.meta(name="viewport", content="width=device-width, initial-scale=1")

    for awesome in papis.config.getlist("serve-font-awesome-css"):
        t.link(rel="stylesheet",
               href=awesome,
               crossorigin="anonymous",
               referrerpolicy="no-referrer")

    t.link(href=papis.config.getstring("serve-bootstrap-css"),
           rel="stylesheet",
           crossorigin="anonymous")
    t.script(type="text/javascript",
             src=papis.config.getstring("serve-bootstrap-js"),
             crossorigin="anonymous")
    t.script(type="text/javascript",
             src=papis.config.getstring("serve-jquery-js"))
    t.link(rel="stylesheet",
           type="text/css",
           href=papis.config.getstring("serve-jquery.dataTables-css"))
    t.script(type="text/javascript",
             charset="utf8",
             src=papis.config.getstring("serve-jquery.dataTables-js"))

    papis.web.latex.katex_header()

    if papis.config.getboolean("serve-enable-timeline"):
        t.link(rel="stylesheet",
               type="text/css",
               href=papis.config.getstring("serve-timeline-css"))
        t.script(type="text/javascript",
                 charset="utf8",
                 src=papis.config.getstring("serve-timeline-js"))

    for src in papis.config.getlist("serve-ace-urls"):
        t.script(type="text/javascript",
                 charset="utf8",
                 src=src)

    for href in papis.config.getlist("serve-user-css"):
        t.link(rel="stylesheet", type="text/css", href=href)

    for src in papis.config.getlist("serve-user-js"):
        t.script(type="text/javascript", src=src)


def main_html_document(pretitle: str) -> t.html_tag:
    with dominate.document(title=None) as result:
        with result.head:
            header(pretitle)
    return result
