import os.path

import dominate.tags as t

import papis.web.html as wh
import papis.web.static

VIEWER_PATH = "epubjs-reader/reader/index.html"
EPUBJS_URL = "https://github.com/futurepress/epubjs-reader"


def detect_local_installation() -> bool:
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
the papis web applications you need to install epubjs-reader.

You can download the EPUBJS bundle from the url

    {EPUBJS_URL}

and extract it to your config directory under 'web/epubjs-reader', for instance
in '~/.config/papis/web/epubjs-reader/'.

On linux and mac you can simply run the following lines

    mkdir -p ~/.config/papis/web/
    git clone {EPUBJS_URL} ~/.config/papis/web/epubjs-reader
    """


def widget(unquoted_file_path: str) -> None:
    """
    Widget for epub files.
    """

    viewer_path = f"/static/{VIEWER_PATH}?bookPath={unquoted_file_path}"

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

    if detect_local_installation():
        t.iframe(src=viewer_path,
                 style="resize: vertical",
                 width="100%",
                 height="800")
    else:
        t.pre(error_message(), cls="alert alert-warning")
