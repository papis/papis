import re
from typing import Dict, Optional, Any, List

import papis.document
import papis.downloaders
import papis.downloaders.base


def _parse_author_list(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    # NOTE: this seems to be a data structure of the form
    #   entry {
    #       "#name": <key-name>,
    #       "_": <string>,
    #       "$": <dict[str, entry]>,
    #       "$$": <list[entry]>,
    #   }
    #
    # defined recursively, so maybe there's a better way to traverse it,
    # but for now this is sufficient and no need to be too fancy about it.

    if "#name" not in data or "$$" not in data:
        return [{}]

    def _parse_author(author: Dict[str, Any]) -> Dict[str, Any]:
        # NOTE: this seems fairly fragile, so hopefully it won't break too badly
        if "$$" not in author:
            return {}

        names = author["$$"]
        if len(names) < 2:
            return {}

        given, family = names[:2]
        assert given["#name"] == "given-name"
        assert family["#name"] == "surname"

        return {"given": given["_"], "family": family["_"], "affiliation": []}

    assert data["#name"] == "author-group"
    return [_parse_author(a) for a in data["$$"] if a["#name"] == "author"]


def get_full_abstract(soup: List[Dict[str, Any]]) -> str:
    abstract = ""

    for section in soup:
        try:
            for value in list(section.values()):
                if isinstance(value, list):
                    for i, dic in enumerate(value):
                        try:
                            a_section = (i, dic["_"])
                        except Exception:
                            pass

                        if "Abstract" in a_section:
                            a_i = i + 1
                            try:
                                a_dic = value[a_i]
                            except Exception:
                                pass

                            if not abstract:
                                try:
                                    a_key = list(a_dic.keys())[0]
                                    a_list = a_dic[a_key]
                                    abstract = a_list[0]["_"]
                                except Exception:
                                    pass
        except Exception:
            pass

    return abstract


class Downloader(papis.downloaders.Downloader):

    def __init__(self, url: str) -> None:
        super().__init__(
            url, name="sciencedirect",
            expected_document_extension="pdf",
            )

    @classmethod
    def match(cls, url: str) -> Optional[papis.downloaders.Downloader]:
        if re.match(r".*\.sciencedirect\.com.*", url):
            return Downloader(url)
        else:
            return None

    def get_data(self) -> Dict[str, Any]:
        soup = self._get_soup()
        data: Dict[str, Any] = {}

        # get authors
        scripts = soup.find_all(name="script", attrs={"data-iso-key": "_0"})
        self.logger.debug("Found %d scripts with 'data-iso-key=_0'.", len(scripts))

        if len(scripts) == 1:
            import json
            rawdata = json.loads(scripts[0].text)

            data["author_list"] = _parse_author_list(rawdata["authors"]["content"][0])
            data["author"] = papis.document.author_list_to_author(data)

        # get main citation data
        # NOTE: this is second because the data is likely more accurate
        data.update(papis.downloaders.base.parse_meta_headers(soup))
        data["url"] = self.uri

        # Get full abstract
        if rawdata:
            full_abstract = get_full_abstract(rawdata["abstracts"]["content"])
            if full_abstract:
                data["abstract"] = full_abstract

        if "firstpage" in data and "lastpage" in data:
            data["pages"] = "{}-{}".format(data["firstpage"], data["lastpage"])

        if "publication_date" in data:
            data["year"], _, _ = data["publication_date"].split("/")

        return data
