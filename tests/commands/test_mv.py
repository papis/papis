import os
import tempfile

import papis.database

from papis.testing import TemporaryLibrary


def test_mv_run(tmp_library: TemporaryLibrary) -> None:
    from papis.commands.mv import run

    db = papis.database.get()
    docs = db.get_all_documents()

    doc = docs[0]
    title = doc["title"]

    folder = doc.get_main_folder()
    assert folder is not None
    folder = os.path.basename(folder)

    with tempfile.TemporaryDirectory(dir=tmp_library.tmpdir) as new_dir:
        run(doc, new_dir)

        query_doc, = db.query_dict({"title": title})
        assert query_doc.get_main_folder() == os.path.join(new_dir, folder)
