import os
import shutil
import tempfile
from typing import Any, Dict


def create_random_pdf(suffix: str = "", prefix: str = "") -> str:
    with tempfile.NamedTemporaryFile(suffix=suffix, prefix=prefix, delete=False) as fd:
        fd.write("%PDF-1.5%\n".encode())

    return fd.name


def create_random_epub(suffix: str = "", prefix: str = "") -> str:
    buf = bytearray(
        [0x50, 0x4B, 0x3, 0x4]
        + [0x00 for i in range(26)]
        + [0x6D, 0x69, 0x6D, 0x65, 0x74, 0x79, 0x70, 0x65, 0x61, 0x70,
           0x70, 0x6C, 0x69, 0x63, 0x61, 0x74, 0x69, 0x6F, 0x6E, 0x2F,
           0x65, 0x70, 0x75, 0x62, 0x2B, 0x7A, 0x69, 0x70]
        + [0x00 for i in range(1)]
        )

    with tempfile.NamedTemporaryFile(suffix=suffix, prefix=prefix, delete=False) as fd:
        fd.write(bytearray(buf))

    return fd.name


def create_random_file(suffix: str = "", prefix: str = "") -> str:
    with tempfile.NamedTemporaryFile(suffix=suffix, prefix=prefix, delete=False) as fd:
        fd.write("hello".encode())

    return fd.name


def create_real_document(
        data: Dict[str, Any], suffix: str = "") -> Dict[str, Any]:
    from papis.document import Document
    folder = tempfile.mkdtemp(suffix=suffix)
    doc = Document(folder=folder, data=data)
    doc.save()

    assert os.path.exists(doc.get_info_file())
    return doc


test_data = [
    {
        "author": "doc without files",
        "title": "Title of doc without files",
        "year": "1093",
        "_test_files": 0,
    },
    {
        "author": "J. Krishnamurti",
        "title": "Freedom from the known",
        "year": "2009",
        "_test_files": 1,
    }, {
        "author": "K. Popper",
        "doi": "10.1021/ct5004252",
        "title": "The open society",
        "volume": "I",
        "_test_files": 0,
    }, {
        "author": "Turing A. M.",
        "doi": "10.1112/plms/s2-42.1.230",
        "issue": "1",
        "journal": "Proceedings of the London Mathematical Society",
        "note": "First turing machine paper foundation of cs",
        "pages": "230--265",
        "title": "On Computable Numbers with an Application to the Entscheidungsproblem",           # noqa: E501
        "url": "https://api.wiley.com/onlinelibrary/tdm/v1/articles/10.1112%2Fplms%2Fs2-42.1.230",  # noqa: E501
        "volume": "s2-42",
        "year": "1937",
        "_test_files": 2,
    },
    {
        "author": "test_author",
        "title": "Test Document 1",
        "year": "2019",
        "_test_files": 1
    },
    {
        "author": "test_author",
        "title": "Test Document 2",
        "year": "2019",
        "_test_files": 1
    },
]


def get_test_lib_name() -> str:
    return "test-lib"


def setup_test_library() -> None:
    """Set-up a test library for tests
    """
    from papis.config import get_configuration, set_lib, get_lib
    config = get_configuration()
    config["settings"] = {}
    folder = tempfile.mkdtemp(prefix="papis-test-library-")

    from papis.library import Library
    libname = get_test_lib_name()
    lib = Library(libname, [folder])
    set_lib(lib)

    from papis.database import clear_cached
    clear_cached()
    os.environ["XDG_CACHE_HOME"] = tempfile.mkdtemp(
        prefix="papis-test-cache-home-"
    )

    from papis.document import from_data
    for i, data in enumerate(test_data):
        data["files"] = [
            create_random_pdf() for i in range(data.get("_test_files"))
        ]
        doc = from_data(data)
        folder = os.path.join(get_lib().paths[0], str(i))
        os.makedirs(folder)
        assert os.path.exists(folder)
        doc.set_folder(folder)
        doc["files"] = [os.path.basename(f) for f in data["files"]]
        doc.save()
        for f in data["files"]:
            shutil.move(
                f,
                doc.get_main_folder()
            )
        assert os.path.exists(doc.get_main_folder())
        assert os.path.exists(doc.get_info_file())
