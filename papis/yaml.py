import yaml
import logging
import click
import os
from typing import Optional, List, Dict, Any

import papis.utils
import papis.config
import papis.importer
import papis.document

logger = logging.getLogger("yaml")


def data_to_yaml(yaml_path: str, data: Dict[str, Any]) -> None:
    """
    Save data to yaml at path outpath

    :param yaml_path: Path to a yaml file
    :type  yaml_path: str
    :param data: Data in a dictionary
    :type  data: dict
    """
    with open(yaml_path, 'w+') as fd:
        yaml.dump(
            data,
            fd,
            allow_unicode=papis.config.getboolean("info-allow-unicode"),
            default_flow_style=False)


def exporter(documents: List[papis.document.Document]) -> str:
    string = yaml.dump_all(
        [papis.document.to_dict(document) for document in documents],
        allow_unicode=True)
    return str(string)


def yaml_to_data(
        yaml_path: str,
        raise_exception: bool = False) -> Dict[str, Any]:
    """
    Convert a yaml file into a dictionary using the yaml module.

    :param yaml_path: Path to a yaml file
    :type  yaml_path: str
    :returns: Dictionary containing the info of the yaml file
    :rtype:  dict
    :raises ValueError: If a yaml parsing error happens
    """
    with open(yaml_path) as fd:
        try:
            data = yaml.safe_load(fd)
        except Exception as e:
            if raise_exception:
                raise ValueError(e)
            logger.error("Yaml syntax error. %s", e)
            return dict()
        else:
            assert isinstance(data, dict)
            return data


@click.command('yaml')
@click.pass_context
@click.argument('yamlfile', type=click.Path(exists=True))
@click.help_option('--help', '-h')
def explorer(ctx: click.Context, yamlfile: str) -> None:
    """
    Import documents from a yaml file

    Examples of its usage are

    papis explore yaml lib.yaml pick

    """
    logger = logging.getLogger('explore:yaml')
    logger.info("Reading in yaml file '%s'", yamlfile)

    docs = [papis.document.from_data(d)
            for d in yaml.safe_load_all(open(yamlfile))]
    ctx.obj['documents'] += docs

    logger.info('%d documents found', len(docs))


class Importer(papis.importer.Importer):

    """Importer that parses a yaml file"""

    def __init__(self, uri: str) -> None:
        papis.importer.Importer.__init__(self, name='yaml', uri=uri)

    @classmethod
    def match(cls, uri: str) -> Optional[papis.importer.Importer]:
        importer = Importer(uri=uri)
        if os.path.exists(uri) and not os.path.isdir(uri):
            importer.fetch()
            return importer if importer.ctx.data else None
        return None

    @papis.importer.cache
    def fetch(self: papis.importer.Importer) -> Any:
        self.ctx.data = yaml_to_data(self.uri, raise_exception=False)
        if self.ctx:
            self.logger.info("successfully read file '%s'", self.uri)
