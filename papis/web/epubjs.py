import os.path
import urllib.parse

import dominate.tags as t

import papis.web.html as wh
import papis.web.static

EPUBJS_URL = "https://github.com/futurepress/epubjs-reader"
VIEWER_PATH = "epubjs-reader/reader/index.html"


def widget(unquoted_file_path: str) -> None:
    """
    Widget for epub files.
    """

    file_path = urllib.parse.quote(unquoted_file_path, safe="")
    viewer_path = f"/static/{VIEWER_PATH}?bookPath={file_path}"

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

    if detect_epubjs():
        t.iframe(src=viewer_path,
                 style="resize: vertical",
                 width="100%",
                 height="800")
    else:
        t.pre(error_message(), cls="alert alert-warning")


def detect_epubjs() -> bool:
    for path in papis.web.static.static_paths():
        viewer = os.path.join(path, VIEWER_PATH)
        if os.path.exists(viewer):
            return True
    return False


def error_message() -> str:
    """Error message for when there is no epubjs-reader installation"""
    return f"""
No installation of epubjs found.

If you want to be able to read and see EPUB files from within
the Papis web applications you need to install epubjs-reader.

You can download the EPUBJS bundle from the url

    {EPUBJS_URL}

and extract it to your config directory under 'web/epubjs-reader', for instance
in '~/.config/papis/web/epubjs-reader/'.

On linux and mac you can simply run the following lines

    mkdir -p ~/.config/papis/web/
    git clone {EPUBJS_URL} ~/.config/papis/web/epubjs-reader
    """
