import re
from typing import List, Union, Dict

import dominate.tags as t

import papis.web.header
import papis.web.navbar
import papis.web.html as wh

Tags = Union[str, List[str]]
TAGS_SPLIT_RX = re.compile(r"\s*[,\s]\s*")
PAPIS_TAGS_CLASS = "papis-tags"
PAPIS_TAG_CLASS = "papis-tag"


def ensure_tags_list(tags: Tags) -> List[str]:
    """
    Ensure getting a list of tags to render them.
    """
    if isinstance(tags, list):
        return tags
    return TAGS_SPLIT_RX.split(tags)


def _tag(tag: str, libname: str) -> t.html_tag:
    return t.a(tag,
               cls="badge bg-dark " + PAPIS_TAG_CLASS,
               href=("/library/{libname}/query?q=tags:{0}"
                     .format(tag, libname=libname)))


def tags_list_div(tags: Tags, libname: str) -> None:
    with t.span(cls=PAPIS_TAGS_CLASS):
        wh.icon("hashtag")
        for tag in papis.web.tags.ensure_tags_list(tags):
            _tag(tag=tag, libname=libname)


def html(pretitle: str, libname: str, tags: Dict[str, int]) -> t.html_tag:
    with papis.web.header.main_html_document(pretitle) as result:
        with result.body:
            papis.web.navbar.navbar(libname=libname)
            with wh.container():
                with t.h1("TAGS"):
                    with t.a(href="/library/{}/tags/refresh".format(libname)):
                        wh.icon("refresh")
                with wh.container():
                    for tag in sorted(tags,
                                      key=lambda k: tags[k],
                                      reverse=True):
                        _tag(tag=tag, libname=libname)
    return result
