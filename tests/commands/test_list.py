import os

import papis.database

from papis.testing import TemporaryLibrary


def test_list_run(tmp_library: TemporaryLibrary) -> None:
    from papis.commands.list import run

    assert papis.config.get_lib_name() == tmp_library.libname

    db = papis.database.get()
    docs = db.get_all_documents()

    objs = run(docs, info_files=True)
    assert len(objs) == len(docs)
    assert all(os.path.exists(f) for f in objs)

    objs = run(docs, notes=True)
    assert len(objs) == 0

    libs = run([], libraries=True)
    assert len(libs) == 1

    folders = run(docs, folders=True)
    assert len(folders) == len(docs)
    assert all(os.path.exists(f) for f in folders)

    ids = run(docs, papis_id=True)
    assert len(ids) == len(docs)
