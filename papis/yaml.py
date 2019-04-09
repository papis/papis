import yaml
import logging
import papis.config
import papis.importer
import click
import papis.utils

logger = logging.getLogger("yaml")


def data_to_yaml(yaml_path, data):
    """
    Save data to yaml at path outpath

    :param yaml_path: Path to a yaml file
    :type  yaml_path: str
    :param data: Data in a dictionary
    :type  data: dict
    """
    global logger
    with open(yaml_path, 'w+') as fd:
        yaml.dump(
            data,
            fd,
            allow_unicode=papis.config.getboolean("info-allow-unicode"),
            default_flow_style=False
        )


def yaml_to_data(yaml_path):
    """
    Convert a yaml file into a dictionary using the yaml module.

    :param yaml_path: Path to a yaml file
    :type  yaml_path: str
    :returns: Dictionary containing the info of the yaml file
    :rtype:  dict
    """
    global logger
    with open(yaml_path) as fd:
        try:
            data = yaml.safe_load(fd)
        except Exception as e:
            logger.error(
                'Error reading yaml file in {0}'.format(yaml_path) +
                '\nPlease check it!\n\n{0}'.format(str(e))
            )
            return dict()
        else:
            return data


@click.command('yaml')
@click.pass_context
@click.argument('yamlfile', type=click.Path(exists=True))
@click.help_option('--help', '-h')
def explorer(ctx, yamlfile):
    """
    Import documents from a yaml file

    Examples of its usage are

    papis explore yaml lib.yaml pick

    """
    logger = logging.getLogger('explore:yaml')
    logger.info('reading in yaml file {}'.format(yamlfile))
    docs = [
        papis.document.from_data(d) for d in yaml.load_all(open(yamlfile))
    ]
    ctx.obj['documents'] += docs
    logger.info('{} documents found'.format(len(docs)))


class Importer(papis.importer.Importer):

    def __init__(self, **kwargs):
        papis.importer.Importer.__init__(self, name='yaml', **kwargs)

    @classmethod
    def match(cls, uri):
        return (
            Importer(uri=uri)
            if papis.utils.get_document_extension(uri) == 'yaml'
            else None
        )

    def fetch(self):
        self.logger.info("Reading input file = %s" % self.uri)
        self.ctx.data = yaml_to_data(self.uri)
