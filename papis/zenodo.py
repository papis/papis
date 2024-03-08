from typing import Any, Dict, List, Optional, TypedDict

import json
import datetime

from markdownify import markdownify

import papis
import papis.utils
import papis.importer
import papis.document
import papis.downloaders.base
from papis.downloaders import download_document

ZENODO_URL = "https://www.zenodo.org/api/records/{record_id}"

# https://docs.citationstyles.org/en/1.0.1/specification.html#appendix-iii-types
logger = papis.logging.get_logger(__name__)


def get_author_info(authors: List[Dict[str, str]]) -> List[Dict[str, str]]:
    out = []
    for author in authors:
        current_author = papis.document.split_author_name(author["name"])
        if affiliation := author.get("affiliation"):
            current_author["affiliation"] = affiliation
        out.append(current_author)
    return out


KeyConversionPair = papis.document.KeyConversionPair
key_conversion = [
    KeyConversionPair(
        "id",
        [
            {"key": "zenodo_record_id", "action": None},
        ],
    ),
    KeyConversionPair("conceptrecid", [{"key": "concept_record_id", "action": None}]),
    KeyConversionPair("doi", [{"key": "doi", "action": None}]),
    KeyConversionPair("title", [{"key": "title", "action": None}]),
    KeyConversionPair("keywords", [{"key": "tags", "action": None}]),
    KeyConversionPair(
        "publication_date",
        [
            {
                "key": "year",
                "action": lambda x: datetime.datetime.fromisoformat(x).year,
            },
            {
                "key": "month",
                "action": lambda x: datetime.datetime.fromisoformat(x).month,
            },
            {"key": "day", "action": lambda x: datetime.datetime.fromisoformat(x).day},
        ],
    ),
    KeyConversionPair("creators", [{"key": "author_list", "action": get_author_info}]),
    KeyConversionPair("links", [{"key": "url", "action": lambda x: x["self"]}]),
    KeyConversionPair("notes", [{"key": "notes", "action": markdownify}]),
    KeyConversionPair("method", [{"key": "method", "action": markdownify}]),
    KeyConversionPair(
        "resource_type", [{"key": "type", "action": lambda x: x["type"]}]
    ),
    KeyConversionPair("revision", [{"key": "revision", "action": None}]),
    KeyConversionPair("license", [{"key": "license", "action": lambda x: x["id"]}]),
    KeyConversionPair("description", [{"key": "description", "action": markdownify}]),
]


def zenodo_data_to_papis_data(data: Dict[str, Any]) -> Dict[str, Any]:
    # Merge metadata into data
    data.update(data["metadata"])
    del data["metadata"]

    new_data = papis.document.keyconversion_to_data(key_conversion, data)
    new_data["file_urls"] = data["files"]

    return new_data


def is_valid_record_id(record_id: str) -> bool:
    record_id = record_id.strip()
    if not record_id.isdigit():
        return False

    with papis.utils.get_session() as session:
        response = session.get(ZENODO_URL.format(record_id=record_id))

    return response.ok


def get_data(query: str = "") -> Dict[str, Any]:
    with papis.utils.get_session() as session:
        response = session.get(
            ZENODO_URL.format(record_id=query.strip()),
            headers={"user-agent": f"papis/{papis.__version__}"},
        )

    try:
        json_data = json.loads(response.content.decode())
    except json.JSONDecodeError as exc:
        logger.error("Failed to decode response from Zenodo.", exc_info=exc)

    return zenodo_data_to_papis_data(json_data)


class LinkInfo(TypedDict):
    """Represents a the url for a Zenodo record.
    Attributes:
    - id, the uuid of the file
    """

    self: str


class FileInfo(TypedDict):
    """Represents a file info entry from a Zenodo record.

    - id, the uuid of the file
    - key, the filename
    - size: the size of a file in bytes
    - checksum: md5sum hash of the file.
    - links: dict with the url to download the file
    """

    id: str
    key: str
    size: int
    checksum: str
    links: LinkInfo


class Importer(papis.importer.Importer):
    """Importer downloading data from a Zenodo ID"""

    def __init__(self, uri: str = "") -> None:
        super().__init__(name="zenodo", uri=uri)
        self._file_urls: List[FileInfo] = []

    @classmethod
    def match(cls, uri: str) -> Optional[papis.importer.Importer]:
        if is_valid_record_id(uri):
            return Importer(uri)

        return None

    @classmethod
    def match_data(cls, data: Dict[str, Any]) -> Optional["Importer"]:
        return None

    def fetch_data(self) -> None:
        self.ctx.data = get_data(self.uri)
        self._file_urls = self.ctx.data["file_urls"]
        del self.ctx.data["file_urls"]

    def fetch_files(self) -> None:
        if not self.ctx.data:
            return

        for url_data in self._file_urls:
            url = url_data["links"]["self"]
            self.logger.info("Trying to download document from '%s'.", url)

            filename = download_document(url, filename=url_data["key"])
            if filename is not None:
                self.ctx.files.append(filename)
