from typing import Any, Callable

import dominate.tags as t


HtmlGiver = Callable[[], t.html_tag]


def fa(name: str, namespace: str = "fa") -> str:
    """
    Font awesome wrapper
    """
    return namespace + " fa-" + name


def flex(where: str, cls: str = "", **kwargs: Any) -> t.html_tag:
    return t.div(cls=cls + " d-flex justify-content-" + where, **kwargs)


def alert(node: t.html_tag, type_: str, **kwargs: Any) -> t.html_tag:
    with node(cls=("alert alert-{} ".format(type_)
                   + "alert-dismissible fade show"),
              role="alert",
              **kwargs) as result:
        t.button(type="button",
                 cls="btn-close",
                 data_bs_dismiss="alert",
                 aria_label="Close")
    return result


def icon(name: str, namespace: str = "fa") -> t.html_tag:
    return t.i(cls=fa(name, namespace=namespace))


def icon_span(icon_name: str, text: str, *fmt: Any, **kfmt: Any) -> None:
    icon(icon_name)
    t.span(text.format(*fmt, **kfmt))


def container() -> t.html_tag:
    return t.div(cls="container")


def modal(body: HtmlGiver, id_: str) -> t.html_tag:
    with t.div(cls="modal fade", tabindex="-1", id=id_) as rst:
        with t.div(cls="modal-dialog"):
            with t.div(cls="modal-content"):
                with t.div(cls="modal-body"):
                    body()
    return rst


def file_icon(filepath: str) -> t.html_tag:
    if filepath.endswith("pdf"):
        return icon("file-pdf")
    if filepath.endswith("jpg") \
       or filepath.endswith("png") \
       or filepath.endswith("gif"):
        return icon("file-image")
    return icon("file")
