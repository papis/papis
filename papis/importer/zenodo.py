from typing import Any

from papis.importer import Context, Importer


class ZenodoContext(Context):
    def __init__(self) -> None:
        super().__init__()
        self.file_info: dict[str, Any] = {}


class ZenodoImporter(Importer):
    """Importer downloading data from a Zenodo ID"""

    ctx: ZenodoContext

    def __init__(self, uri: str = "") -> None:
        super().__init__(name="zenodo", uri=uri, ctx=Context())

    @classmethod
    def match(cls, uri: str) -> "ZenodoImporter | None":
        from papis.zenodo import is_valid_record_id

        if is_valid_record_id(uri):
            return ZenodoImporter(uri)

        return None

    def fetch_data(self) -> None:
        from papis.zenodo import get_data, zenodo_data_to_papis_data

        zenodo_data = get_data(self.uri)
        # Build a filename to URL dictionary
        self.ctx.file_info = {
            file["key"]: file["links"]["self"] for file in zenodo_data["files"]
        }
        self.ctx.data = zenodo_data_to_papis_data(zenodo_data)

    def fetch_files(self) -> None:
        if not self.ctx.file_info:
            return

        from papis.downloaders import download_document

        for filename, url in self.ctx.file_info.items():
            self.logger.info("Trying to download document from '%s'.", url)

            out_filename = download_document(url, filename=filename)
            if out_filename is not None:
                self.ctx.files.append(out_filename)
