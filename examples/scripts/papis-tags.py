#! /usr/bin/env python3
# papis-short-help: Search tags in the library.
# Copyright © 2018 Alejandro Gallo. GPLv3

"""
This commands allows searching tags and selecting documents that match.
A simple usage of this command is just::

    papis tags --no-confirm Einstein

which will first compile a list of all the tags in documents that contain the
``"Einstein"`` query. The user is then prompted to select a tag. This tag
is then used to find all other documents in the library that are tagged with it.
The user is then prompted to select a document and open its main folder.

Papis does not impose any structure on the format of the ``"tags"`` field in
a document. However, for this script the following formats are supported:

* a list of string tags, e.g. ``["tag1", "tag2", "tag3"]
* a comma-separated string of tags, where the tags themselves can contain spaces,
  e.g. ``"tag name 1, tag name 2, tag name 3"``.
* a space-separated string of tags, e.g. ``"tag-name-1 tag-name-2 tag-name-3"``.
"""

import re

import click

from typing import Set

import papis.api
import papis.cli
import papis.document
import papis.logging

papis.logging.setup()
logger = papis.logging.get_logger("papis.commands.tags")

TAG_COMMA_REGEX = re.compile(r"\s*,\s*")
TAG_SPACE_REGEX = re.compile(r"\W+")


@click.command()
@papis.cli.query_argument()
@click.help_option("-h", "--help")
@click.option(
    "--confirm/--no-confirm",
    help="Ask to confirm before adding to the collection",
    flag_value=True,
    is_flag=True,
    default=lambda: papis.config.getboolean("add-confirm"))
def main(query: str, confirm: bool) -> None:
    """
    Search tags of the library and open a document
    """
    documents = papis.api.get_documents_in_lib(
        papis.api.get_lib_name(),
        search=query
    )

    # Create an empty tag list
    tag_list: Set[str] = set()
    for doc in documents:
        tags = doc.get("tags")
        if tags is None:
            continue

        if isinstance(tags, str):
            # NOTE: tags can be either one of
            #   tag name 1, tag name 2, tag name 3
            #   tag-name-1 tag-name-2 tag-name-3
            # i.e. if comma separated, spaces are allowed in
            if "," in tags:
                tags = TAG_COMMA_REGEX.split(tags)
            else:
                tags = TAG_SPACE_REGEX.split(tags)
        elif isinstance(tags, list):
            pass
        else:
            logger.error("'tags' key has unknown type '%s': '%s'",
                         type(tags).__name__, papis.document.describe(doc))
            continue

        tag_list = tag_list | set(tags)

    # if no tags are found, exit gracefully
    if not tag_list:
        logger.info("The selected documents do not have any tags set.")
        return

    # Allow the list set (no duplicates) ) to be sorted into alphabetical
    # order and picked from
    sorted_tags = sorted(list(tag_list))
    picked_tags = papis.api.pick(sorted_tags)
    if len(picked_tags) == 1:
        picked_tag, = picked_tags
    else:
        logger.error("Picked multiple tags (selecting first one): '%s'",
                     "', '".join(picked_tags))
        picked_tag = picked_tags[0]

    logger.info("Picked tag '%s'", picked_tag)
    docs = papis.api.get_documents_in_lib(search={"tags": picked_tag})
    docs = list(papis.api.pick_doc(docs))

    from papis.tui.utils import confirm as confirm_dialog
    for doc in docs:
        folder = doc.get_main_folder()
        if folder is None:
            continue

        if confirm:
            if not confirm_dialog(
                    "Open folder for '{}'?".format(papis.document.describe(doc))
                    ):
                continue

        papis.api.open_dir(folder, wait=False)


if __name__ == "__main__":
    main()
