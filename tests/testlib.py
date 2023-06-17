import os
import random
import tempfile
from typing import Any, Dict, Sequence, Optional

import pytest
import click
import click.testing

import papis.logging

papis.logging.setup()
random.seed(42)

PAPIS_UPDATE_RESOURCES = os.environ.get("PAPIS_UPDATE_RESOURCES", "none").lower()
if PAPIS_UPDATE_RESOURCES not in ("none", "remote", "local", "both"):
    raise ValueError("unsupported value of 'PAPIS_UPDATE_RESOURCES'")

PAPIS_TEST_DOCUMENTS = [
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
        "type": "article",
        "author": "Turing, A. M.",
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
        "title": "Test Document 1 (wRkdff)",
        "year": "2019",
        "_test_files": 1
    },
    {
        "author": "test_author",
        "title": "Test Document 2 (ZD9QRz)",
        "year": "2019",
        "_test_files": 1
    },
]


def create_random_file(filetype: Optional[str] = None,
                       prefix: Optional[str] = None,
                       suffix: Optional[str] = None,
                       dir: Optional[str] = None) -> str:
    if filetype is None:
        filetype = random.choice(["pdf", "epub", "djvu"])

    # NOTE: these are chosen to match using 'filetype.guess' and are not valid
    # files otherwise
    if filetype == "pdf":
        buf = b"%PDF-1.5%\n"
        suffix = ".pdf" if suffix is None else suffix
    elif filetype == "epub":
        buf = bytes(
            [0x50, 0x4B, 0x3, 0x4]
            + [0x00 for i in range(26)]
            + [0x6D, 0x69, 0x6D, 0x65, 0x74, 0x79, 0x70, 0x65, 0x61, 0x70,
                0x70, 0x6C, 0x69, 0x63, 0x61, 0x74, 0x69, 0x6F, 0x6E, 0x2F,
                0x65, 0x70, 0x75, 0x62, 0x2B, 0x7A, 0x69, 0x70]
            + [0x00 for i in range(1)]
            )
        suffix = ".epub" if suffix is None else suffix
    elif filetype == "djvu":
        buf = bytes(
            [0x41, 0x54, 0x26, 0x54, 0x46, 0x4F, 0x52, 0x4D]
            + [0x00, 0x00, 0x00, 0x00]
            + [0x44, 0x4A, 0x56, 0x4D]
            )
        suffix = ".djvu" if suffix is None else suffix
    elif filetype == "text":
        buf = b"papis-test-file-contents"
    else:
        raise ValueError("Unknown file type: '{}'".format(filetype))

    with tempfile.NamedTemporaryFile(
            dir=dir, suffix=suffix, prefix=prefix,
            delete=False) as fd:
        fd.write(buf)

    return fd.name


def populate_library(libdir: str) -> None:
    import papis.id
    from papis.document import Document

    for i, data in enumerate(PAPIS_TEST_DOCUMENTS):
        doc_data = data.copy()

        folder_path = os.path.join(libdir, "test_doc_{}".format(i))
        os.makedirs(folder_path)

        # add files
        num_test_files = doc_data.pop("_test_files")
        if num_test_files:
            doc_data["files"] = [
                os.path.basename(create_random_file(dir=folder_path))
                for _ in range(num_test_files)
                ]

        # create document
        doc = Document(folder_path, doc_data)
        doc[papis.id.key_name()] = papis.id.compute_an_id(doc)
        doc.save()


class TemporaryConfiguration:
    libname = "test"

    def __init__(self,
                 settings: Optional[Dict[str, Any]] = None,
                 overwrite: bool = False) -> None:
        self.settings = settings
        self.overwrite = overwrite

        self.libdir = ""
        self.configdir = ""
        self.configfile = ""

        self._tmpdir: Optional[tempfile.TemporaryDirectory] = None
        self._monkeypatch: Optional[pytest.MonkeyPatch] = None

    @property
    def tmpdir(self) -> str:
        return self._tmpdir.name

    def create_random_file(self,
                           filetype: Optional[str] = None,
                           prefix: Optional[str] = None,
                           suffix: Optional[str] = None) -> str:
        return create_random_file(
            filetype, suffix=suffix, prefix=prefix,
            dir=self.tmpdir)

    def __enter__(self) -> "TemporaryConfiguration":
        if self._tmpdir is not None:
            raise ValueError("{!r} cannot be nested".format(type(self).__name__))

        # create directories and files
        self._tmpdir = tempfile.TemporaryDirectory(prefix="papis-test-")

        self.libdir = os.path.join(self.tmpdir, "lib")
        self.configdir = os.path.join(self.tmpdir, "papis")
        self.configfile = os.path.join(self.configdir, "config")

        os.makedirs(self.libdir)
        os.makedirs(self.configdir)
        os.makedirs(os.path.join(self.configdir, "scripts"))

        # load settings
        settings = {
            self.libname: {"dir": self.libdir},
            "settings": {"default-library": self.libname}
        }

        if self.settings is not None:
            if self.overwrite:
                settings = self.settings
            else:
                settings["settings"].update(self.settings)

        import configparser
        with open(self.configfile, "w") as fd:
            config = configparser.ConfigParser()
            config.read_dict(settings)
            config.write(fd)

        # monkeypatch environment
        self._monkeypatch = pytest.MonkeyPatch()
        self._monkeypatch.setenv("XDG_CONFIG_HOME", self.tmpdir)
        self._monkeypatch.setenv("XDG_CACHE_HOME", self.tmpdir)

        # reload configuration
        import papis.config
        papis.config.set_config_file(self.configfile)
        papis.config.reset_configuration()

        assert papis.config.get_config_folder() == self.configdir
        assert papis.config.get_config_file() == self.configfile

        return self

    def __exit__(self, exc_type, exc_value, exc_traceback) -> None:
        # cleanup
        self._monkeypatch.undo()
        self._tmpdir.cleanup()

        # reset variables
        self._tmpdir = None
        self.libdir = ""
        self.configdir = ""
        self.configfile = ""


class TemporaryLibrary(TemporaryConfiguration):
    def __init__(self,
                 settings: Optional[Dict[str, Any]] = None,
                 populate: bool = True) -> None:
        super().__init__(settings=settings)
        self.populate = populate

    def __enter__(self) -> "TemporaryLibrary":
        super().__enter__()

        # initialize library
        import papis.library
        lib = papis.library.Library(self.libname, [self.libdir])

        import papis.config
        papis.config.set("default-library", self.libname)
        papis.config.set_lib(lib)

        # populate library
        if self.populate:
            populate_library(self.libdir)

        return self


class PapisRunner(click.testing.CliRunner):
    def __init__(self, **kwargs: Any) -> None:
        if "mix_stderr" not in kwargs:
            kwargs["mix_stderr"] = False

        super().__init__(**kwargs)

    def invoke(self,
               cli: click.Command,
               args: Sequence[str], **kwargs: Any) -> click.testing.Result:
        if "catch_exceptions" not in kwargs:
            kwargs["catch_exceptions"] = False

        return super().invoke(cli, args, **kwargs)


class ResourceCache:
    def __init__(self, cachedir: str) -> None:
        import papis.utils

        self.cachedir = os.path.join(os.path.dirname(__file__), cachedir)
        if not os.path.exists(self.cachedir):
            os.makedirs(self.cachedir)

        self.session = papis.utils.get_session()

    def get_remote_resource(
            self, filename: str, url: str,
            force: bool = False,
            params: Optional[Dict[str, str]] = None,
            headers: Optional[Dict[str, str]] = None,
            cookies: Optional[Dict[str, str]] = None,
            ) -> bytes:
        filename = os.path.join(self.cachedir, filename)
        if force or PAPIS_UPDATE_RESOURCES in ("remote", "both"):
            if headers is None:
                headers = {}

            response = self.session.get(
                url, params=params, headers=headers, cookies=cookies)

            with open(filename, "w", encoding="utf-8") as f:
                f.write(response.content.decode())

        with open(filename, encoding="utf-8") as f:
            return f.read().encode()

    def get_local_resource(
            self, filename: str, data: Any,
            force: bool = False) -> Any:
        filename = os.path.join(self.cachedir, filename)
        _, ext = os.path.splitext(filename)

        import json
        import yaml
        import papis.yaml

        if force or PAPIS_UPDATE_RESOURCES in ("local", "both"):
            assert data is not None
            with open(filename, "w", encoding="utf-8") as f:
                if ext == ".json":
                    json.dump(
                        data, f,
                        indent=2,
                        sort_keys=True,
                        ensure_ascii=False,
                        )
                elif ext == ".yml" or ext == ".yaml":
                    yaml.dump(
                        data, f,
                        indent=2,
                        sort_keys=True,
                        )
                else:
                    raise ValueError("Unknown file extension: '{}'".format(ext))

        with open(filename, encoding="utf-8") as f:
            if ext == ".json":
                return json.load(f)
            elif ext == ".yml" or ext == ".yaml":
                return papis.yaml.yaml_to_data(filename)
            else:
                raise ValueError("Unknown file extension: '{}'".format(ext))
