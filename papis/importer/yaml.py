import os

from papis.importer import Importer


class YAMLImporter(Importer):
    """Importer that parses a YAML file."""

    def __init__(self, uri: str) -> None:
        super().__init__(name="yaml", uri=uri)

    @classmethod
    def match(cls, uri: str) -> "YAMLImporter | None":
        """Check if the *uri* points to an existing YAML file."""
        importer = None
        if os.path.exists(uri) and not os.path.isdir(uri):
            _, ext = os.path.splitext(uri)
            if ext in {".yml", ".yaml"}:
                importer = YAMLImporter(uri)

        return importer

    def fetch_data(self) -> None:
        """Fetch metadata from the YAML file."""
        from papis.yaml import yaml_to_data

        self.ctx.data = yaml_to_data(self.uri, raise_exception=True)
        if self.ctx:
            self.logger.debug("Successfully read file: '%s'.", self.uri)
