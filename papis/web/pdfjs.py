import os.path
import urllib.parse

import dominate.tags as t

import papis.web.html as wh
import papis.web.static

PDFJS_URL = ("https://github.com/mozilla/pdf.js/releases/download/"
             "v3.1.81/pdfjs-3.1.81-legacy-dist.zip")
VIEWER_PATH = "pdfjs/web/viewer.html"


def widget(unquoted_file_path: str) -> None:
    """
    Widget for pdf files.
    """

    file_path = urllib.parse.quote(unquoted_file_path, safe="")
    viewer_path = (f"/static/{VIEWER_PATH}?file={file_path}")

    with wh.flex("center"):
        with t.div(cls="btn-group", role="group"):
            with t.a(href=viewer_path,
                     cls="btn btn-outline-success",
                     target="_blank"):
                wh.icon_span("square-arrow-up-right", "Open in new window")
            with t.a(href=unquoted_file_path,
                     cls="btn btn-outline-success",
                     target="_blank"):
                wh.icon_span("download", "Download")

    if detect_pdfjs():
        t.iframe(src=viewer_path,
                 style="resize: vertical",
                 width="100%",
                 height="800")
    else:
        t.pre(error_message(), cls="alert alert-warning")


def detect_pdfjs() -> bool:
    for path in papis.web.static.static_paths():
        viewer = os.path.join(path, VIEWER_PATH)
        if os.path.exists(viewer):
            return True
    return False


def error_message() -> str:
    """Error message for when there is no pdfjs installation"""
    return f"""
No installation of pdfjs found.

If you want to be able to read and see PDF files from within
the Papis web applications you need to install pdfjs.

You can download the PDFJS bundle from the url

    {PDFJS_URL}

and extract it to your config directory under 'web/pdfjs', for instance
in '~/.config/papis/web/pdfjs/'.

On linux and mac you can simply run the following lines

    mkdir -p ~/.config/papis/web/pdfjs
    cd ~/.config/papis/web/pdfjs
    wget "{PDFJS_URL}" -O pdfjs.zip
    unzip pdfjs.zip
    rm pdfjs.zip
    """
