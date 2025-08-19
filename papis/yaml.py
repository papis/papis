import os
from collections.abc import Sequence
from typing import Any

import yaml

import papis.config
import papis.document
import papis.importer
import papis.logging
import papis.utils

# NOTE: try to use the CLoader when possible, as it's a lot faster than the
# python version, at least at the time of writing
try:
    from yaml import CSafeDumper as Dumper, CSafeLoader as Loader
except ImportError:
    from yaml import (  # type: ignore[assignment]
        SafeDumper as Dumper,
        SafeLoader as Loader,
    )

logger = papis.logging.get_logger(__name__)


def data_to_yaml(yaml_path: str,
                 data: dict[str, Any], *,
                 allow_unicode: bool | None = True) -> None:
    """Save *data* to *yaml_path* in the YAML format.

    :param yaml_path: path to a file.
    :param data: data to write to the file as a YAML document.
    """
    with open(yaml_path, "w+", encoding="utf-8") as fd:
        yaml.dump(data,
                  stream=fd,
                  Dumper=Dumper,
                  allow_unicode=allow_unicode,
                  default_flow_style=False)


def list_to_path(data: Sequence[dict[str, Any]],
                 filepath: str, *,
                 allow_unicode: bool | None = True) -> None:
    r"""Save a list of :class:`dict`\ s to a YAML file.

    :param data: a sequence of dictionaries to save as YAML documents.
    :param filepath: path to a file.
    """
    with open(filepath, "w+", encoding="utf-8") as fd:
        yaml.dump_all(data,
                      stream=fd,
                      Dumper=Dumper,
                      allow_unicode=allow_unicode,
                      default_flow_style=False)


def yaml_to_data(yaml_path: str,
                 raise_exception: bool = False) -> dict[str, Any]:
    """Read a YAML document from *yaml_path*.

    :param yaml_path: path to a file.
    :param raise_exception: if *True* an exception is raised when loading the
        data has failed. Otherwise just a log message is emitted.
    :returns: a :class:`dict` containing the data from the YAML document.

    :raises ValueError: if the document cannot be loaded due to YAML parsing errors.
    """

    with open(yaml_path, encoding="utf-8") as fd:
        try:
            data = yaml.load(fd, Loader=Loader)
        except Exception as exc:
            if raise_exception:
                raise ValueError(exc) from exc
            logger.error("YAML syntax error.", exc_info=exc)
            return {}
        else:
            assert isinstance(data, dict)
            return data


def yaml_to_list(yaml_path: str,
                 raise_exception: bool = False) -> list[dict[str, Any]]:
    """Read a list of YAML documents.

    This is analogous to :func:`yaml_to_data`, but uses ``yaml.load_all`` to
    read multiple documents (see
    `PyYAML docs <https://pyyaml.org/wiki/PyYAMLDocumentation>`__).

    :param yaml_path: path to a file containing YAML documents.
    :param raise_exception: if *True* an exception is raised when loading the
        data has failed. Otherwise just a log message is emitted.
    :returns: a :class:`list` of :class:`dict` objects, one for each YAML
        document in the file.

    :raises ValueError: if the documents cannot be loaded due to YAML parsing errors.
    """
    try:
        with open(yaml_path, encoding="utf-8") as fd:
            return list(yaml.load_all(fd, Loader=Loader))
    except Exception as exc:
        if raise_exception:
            raise ValueError(exc) from exc
        logger.error("YAML syntax error. %s", exc_info=exc)
        return []


class Importer(papis.importer.Importer):

    """Importer that parses a YAML file."""

    def __init__(self, uri: str) -> None:
        super().__init__(name="yaml", uri=uri)

    @classmethod
    def match(cls, uri: str) -> papis.importer.Importer | None:
        """Check if the *uri* points to an existing YAML file."""
        importer = Importer(uri=uri)
        if os.path.exists(uri) and not os.path.isdir(uri):
            importer.fetch()
            return importer if importer.ctx.data else None
        return None

    def fetch_data(self: papis.importer.Importer) -> Any:
        """Fetch metadata from the YAML file."""
        self.ctx.data = yaml_to_data(self.uri, raise_exception=True)
        if self.ctx:
            self.logger.debug("Successfully read file: '%s'.", self.uri)
