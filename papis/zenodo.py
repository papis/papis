import datetime
import json
from typing import Any, Dict, List, Optional, TypedDict

import papis
import papis.document
import papis.downloaders.base
import papis.importer
import papis.utils
from papis.downloaders import download_document

ZENODO_URL = "https://www.zenodo.org/api/records/{record_id}"

logger = papis.logging.get_logger(__name__)


def get_author_info(authors: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Formats each of the authors as a dictionary with given name,
    family name, and affiliation if available.

    :param authors: The list of authors

    :return: A list of formatted authors
    """
    out = []
    for author in authors:
        current_author = papis.document.split_author_name(author["name"])
        if affiliation := author.get("affiliation"):
            current_author["affiliation"] = affiliation
        out.append(current_author)
    return out


def get_text_from_html(html: str) -> str:
    """
    Processes the HTML and returns it in markdown format if a dependency is found,
    or raw HTML otherwise.

    :param html: The raw HTML as embedded in the incoming Zenodo JSON data.
    :return: Either the raw HTML as text, or the markdown-annotated plain text.
    """
    try:
        from markdownify import markdownify  # type: ignore[import-untyped]

        result = markdownify(html)  # type: str
        return result

    except ImportError:
        logger.info(
            "Saving text as raw HTML.  Install `markdownify` to convert it to markdown."
        )
        return html


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
    KeyConversionPair("notes", [{"key": "notes", "action": get_text_from_html}]),
    KeyConversionPair("method", [{"key": "method", "action": get_text_from_html}]),
    KeyConversionPair(
        "resource_type", [{"key": "type", "action": lambda x: x["type"]}]
    ),
    KeyConversionPair("revision", [{"key": "revision", "action": None}]),
    KeyConversionPair("license", [{"key": "license", "action": lambda x: x["id"]}]),
    KeyConversionPair(
        "description", [{"key": "description", "action": get_text_from_html}]
    ),
]


def zenodo_data_to_papis_data(data: Dict[str, Any]):
    """Converts the dictionary from Zenodo to the conventional papis format.

    :param data: the raw dictionary from Zenodo
    :return: a new dictionary in a conventional papis form
    """
    # Merge metadata into data
    data.update(data["metadata"])
    del data["metadata"]

    new_data = papis.document.keyconversion_to_data(key_conversion, data)
    new_data["files"] = data["files"]

    return new_data


def is_valid_record_id(record_id: str) -> bool:
    """Checks if a record is a valid Zenodo record, first checking its form and then
    testing against Zenodo

    :param record_id: a Zenodo record id
    :return: whether the record is valid
    """
    record_id = record_id.strip()
    if not record_id.isdigit():
        return False

    with papis.utils.get_session() as session:
        response = session.get(ZENODO_URL.format(record_id=record_id))

    return response.ok


def get_data(record_id: str) -> Dict[str, Any]:
    """Fetches a record from the Zenodo API and processes it with a helper function

    :param record_id: a Zenodo record id
    :return: a processed zenodo record
    """
    with papis.utils.get_session() as session:
        response = session.get(
            ZENODO_URL.format(record_id=record_id.strip()),
            headers={"user-agent": f"papis/{papis.__version__}"},
        )

    try:
        json_data = json.loads(response.content.decode())
    except json.JSONDecodeError as exc:
        logger.error("Failed to decode response from Zenodo.", exc_info=exc)

    return json_data


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

    @classmethod
    def match(cls, uri: str) -> Optional[papis.importer.Importer]:
        if is_valid_record_id(uri):
            return Importer(uri)

        return None

    @classmethod
    def match_data(cls, data: Dict[str, Any]) -> Optional["Importer"]:
        return None

    def fetch_data(self) -> None:
        zenodo_data = get_data(self.uri)
        self.ctx.data = zenodo_data_to_papis_data(zenodo_data)
        self.ctx.files = self.ctx.data["files"]
        del self.ctx.data["files"]

    def fetch_files(self) -> None:
        if not self.ctx.files:
            return

        for url_data in self.ctx.files:
            url = url_data["links"]["self"]
            self.logger.info("Trying to download document from '%s'.", url)

            out_filename = download_document(url, filename=filename)
            if out_filename is not None:
                self.ctx.files.append(out_filename)
