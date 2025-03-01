import os
from typing import Optional, List, Dict, Any, Sequence

import yaml
import click

import papis.utils
import papis.config
import papis.importer
import papis.document
import papis.logging

# NOTE: try to use the CLoader when possible, as it's a lot faster than the
# python version, at least at the time of writing
try:
    from yaml import CSafeDumper as Dumper, CSafeLoader as Loader
except ImportError:
    from yaml import SafeDumper as Dumper  # type: ignore[assignment]
    from yaml import SafeLoader as Loader  # type: ignore[assignment]

logger = papis.logging.get_logger(__name__)


def data_to_yaml(yaml_path: str,
                 data: Dict[str, Any], *,
                 allow_unicode: Optional[bool] = True) -> None:
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


def list_to_path(data: Sequence[Dict[str, Any]],
                 filepath: str, *,
                 allow_unicode: Optional[bool] = True) -> None:
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
                 raise_exception: bool = False) -> Dict[str, Any]:
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
                 raise_exception: bool = False) -> List[Dict[str, Any]]:
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


def exporter(documents: List[papis.document.Document]) -> str:
    """Convert document to the YAML format"""
    string = yaml.dump_all(
        [papis.document.to_dict(document) for document in documents],
        allow_unicode=True)

    return str(string)


@click.command("yaml")
@click.pass_context
@click.argument("yamlfile", type=click.Path(exists=True))
@click.help_option("--help", "-h")
def explorer(ctx: click.Context, yamlfile: str) -> None:
    """Import documents from a YAML file.

    For example, you can call

        papis explore yaml 'lib.yaml' pick
    """
    logger.info("Reading YAML file '%s'...", yamlfile)

    with open(yamlfile, encoding="utf-8") as fd:
        docs = [papis.document.from_data(d)
                for d in yaml.load_all(fd, Loader=Loader)]
    ctx.obj["documents"] += docs

    logger.info("Found %d documents.", len(docs))


class Importer(papis.importer.Importer):

    """Importer that parses a YAML file"""

    def __init__(self, uri: str) -> None:
        super().__init__(name="yaml", uri=uri)

    @classmethod
    def match(cls, uri: str) -> Optional[papis.importer.Importer]:
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
