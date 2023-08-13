import string

import dominate.tags as t
import dominate.util as tu

DJVUJS_LIB_SRC = "https://djvu.js.org/assets/dist/djvu.js"
DJVUJS_VIEWER_SRC = "https://djvu.js.org/assets/dist/djvu_viewer.js"
MAIN_CODE = string.Template("""
window.onload = async function () {
    let element = document.querySelector("#$selector");
    window.djvu_viewer_instance = new DjVu.Viewer();
    window.djvu_viewer_instance.render(element);
    await window.djvu_viewer_instance.loadDocumentByUrl('$path');
}
""")


def widget(_unquoted_file_path: str, viewer_id: str = "djvuViewer") -> None:
    """
    Widget for pdfjs.

    It includes the djvu javascript library from the internet, maybe
    change this in the future.
    It can in principle create several viewers by giving a different viewer_id
    argument.
    """
    t.div(id=viewer_id)
    t.script(tu.raw(MAIN_CODE.substitute(**dict(selector=viewer_id,
                                                path=_unquoted_file_path))))

    t.script(src=DJVUJS_LIB_SRC)
    t.script(src=DJVUJS_VIEWER_SRC)
