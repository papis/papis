import os

import papis.database

from papis.testing import TemporaryLibrary


def test_list_run(tmp_library: TemporaryLibrary) -> None:
    from papis.commands.list import list_plugins, list_documents

    assert papis.config.get_lib_name() == tmp_library.libname

    db = papis.database.get()
    docs = db.get_all_documents()

    objs = list_documents(docs, show_info=True)
    assert len(objs) == len(docs)
    assert all(os.path.exists(f) for f in objs)

    objs = list_documents(docs, show_notes=True)
    assert len(objs) == 0

    libs = list_plugins(show_libraries=True)
    assert len(libs) == 1

    folders = list_documents(docs, show_dir=True)
    assert len(folders) == len(docs)
    assert all(os.path.exists(f) for f in folders)

    ids = list_documents(docs, show_id=True)
    assert len(ids) == len(docs)
