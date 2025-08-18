import click

import papis.cli
import papis.logging
from papis.explorers import as_explorer

logger = papis.logging.get_logger(__name__)


@as_explorer("yaml")
@click.argument("yamlfile", type=click.Path(exists=True))
def cli(ctx: click.Context, yamlfile: str) -> None:
    """Import documents from a YAML file.

    For example, you can call:

    .. code:: sh

        papis explore yaml 'lib.yaml' pick
    """
    logger.info("Reading YAML file '%s'...", yamlfile)

    import yaml

    try:
        from yaml import CSafeLoader as Loader
    except ImportError:
        from yaml import SafeLoader as Loader  # type: ignore[assignment]

    with open(yamlfile, encoding="utf-8") as fd:
        docs = [papis.document.from_data(d)
                for d in yaml.load_all(fd, Loader=Loader)]
    ctx.obj["documents"] += docs

    logger.info("Found %d documents.", len(docs))
