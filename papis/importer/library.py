import os

from papis.importer import Importer


class FromLibraryImporter(Importer):
    """Importer that gets files and data from a Papis library."""

    def __init__(self, uri: str) -> None:
        super().__init__(name="lib", uri=uri)

    @classmethod
    def match(cls, uri: str) -> "FromLibraryImporter | None":
        from papis.config import get_lib_from_name

        try:
            get_lib_from_name(uri)
        except Exception:
            return None
        else:
            return FromLibraryImporter(uri)

    def fetch(self) -> None:
        from papis.api import get_all_documents_in_lib
        from papis.pick import pick_doc

        docs = pick_doc(get_all_documents_in_lib(self.uri))
        if not docs:
            return

        folder = docs[0].get_main_folder()
        if folder is None:
            return

        importer = FromFolderImporter(folder)
        importer.fetch()
        self.ctx = importer.ctx


class FromFolderImporter(Importer):
    """Importer that gets files and data from a Papis document folder."""

    def __init__(self, uri: str) -> None:
        super().__init__(name="folder", uri=uri)

    @classmethod
    def match(cls, uri: str) -> "FromFolderImporter | None":
        return FromFolderImporter(uri=uri) if os.path.isdir(uri) else None

    def fetch(self) -> None:
        self.logger.info("Importing from folder '%s'.", self.uri)

        from papis.document import from_folder, to_dict
        from papis.id import ID_KEY_NAME

        # NOTE: need to delete the ID_KEY_NAME, if it exists, so that it gets
        # regenerated when the document gets added to a library
        doc = from_folder(self.uri)
        doc.pop(ID_KEY_NAME, None)

        self.ctx.data = to_dict(doc)
        self.ctx.files = doc.get_files()
