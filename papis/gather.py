"""Evidence gathering: turn one item of user input into a :class:`GatheredItem`."""

from __future__ import annotations

import os
import posixpath
import tempfile
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING
from urllib.parse import urlsplit

import papis.logging
from papis.sources.handler import LookupInput

if TYPE_CHECKING:
    import requests

logger = papis.logging.get_logger(__name__)

#: Timeout (in seconds) for fetching webpages.
PAGE_TIMEOUT = 30

_TEMP_DIR = tempfile.TemporaryDirectory(prefix="papis-downloads-")


@dataclass
class GatheredItem:
    """The outcome of gathering a single item of user input.

    :param evidence: the facts gathered from the item.
    :param local_files: local files to attach to the created document.
    """

    evidence: LookupInput
    local_files: list[str] = field(default_factory=list)


#: An extractor turns a local file into identifier fields.
Extractor = Callable[[str], dict[str, str]]

_EXTRACTORS: dict[str, list[Extractor]] = {}


def register_extractor(extension: str, extractor: Extractor) -> None:
    """Register a client-side *extractor* for files with the given *extension*.

    :param extension: a file extension without the leading dot.
    :param extractor: a callable turning a file path into identifier fields.
    """
    _EXTRACTORS.setdefault(extension, []).append(extractor)


def _extract_pdf_doi(path: str) -> dict[str, str]:
    from doi import pdf_to_doi

    doi = pdf_to_doi(path, maxlines=200)
    return {"doi": doi} if doi else {}


def _extract_pdf_arxivid(path: str) -> dict[str, str]:
    from papis.arxiv import pdf_to_arxivid

    arxivid = pdf_to_arxivid(path, maxlines=2000)
    return {"eprint": arxivid, "eprinttype": "arxiv"} if arxivid else {}


register_extractor("pdf", _extract_pdf_doi)
register_extractor("pdf", _extract_pdf_arxivid)


def extract_fields(path: str) -> dict[str, str]:
    """Run the extractors registered for *path* and collect their fields.

    :param path: a local file path.
    :returns: the extracted identifier fields, empty when none are found.
    """
    extension = os.path.splitext(path)[1].lstrip(".").lower()
    fields: dict[str, str] = {}

    for extractor in _EXTRACTORS.get(extension, []):
        try:
            extracted = extractor(path)
        except Exception as exc:
            logger.warning(
                "Extractor for '.%s' files failed on '%s'.",
                extension,
                path,
                exc_info=exc,
            )
            continue

        for key, value in extracted.items():
            if key not in fields and value:
                logger.info("Extracted %s '%s' from file '%s'.", key, value, path)
                fields[key] = value

    return fields


def _request(url: str) -> requests.Response | None:
    """GET *url* and return the response, or ``None`` on failure."""
    from requests.exceptions import RequestException

    from papis.utils import get_session

    try:
        with get_session() as session:
            response = session.get(url, timeout=PAGE_TIMEOUT)
    except RequestException as exc:
        logger.error("Could not fetch '%s'.", url, exc_info=exc)
        return None
    except Exception as exc:
        logger.error("Fetching '%s' failed unexpectedly.", url, exc_info=exc)
        return None

    if not response.ok:
        logger.error(
            "Could not fetch '%s'. (HTTP status: %s %d).",
            url,
            response.reason,
            response.status_code,
        )
        return None

    return response


def _is_html_response(response: requests.Response) -> bool:
    """Whether *response* is an HTML page.

    :param response: a fetched response.
    """
    content_type = response.headers.get("Content-Type", "")
    content_type = content_type.split(";")[0].strip().lower()
    return content_type in {"text/html", "application/xhtml+xml"}


def fetch_metadata_content(url: str) -> str | None:
    """Fetch the text content of the metadata file at *url*, or ``None`` on failure.

    :param url: the URL of the file to fetch.
    :returns: the decoded file text.
    """
    response = _request(url)
    if response is None:
        return None

    if _is_html_response(response):
        logger.warning("'%s' returned an HTML page instead of a file.", url)
        return None

    return response.content.decode("utf-8", errors="replace")


def get_filename_from_response(response: requests.Response) -> str | None:
    """Guess a filename for the payload of *response*."""
    from email.message import EmailMessage

    filename: str | None = None

    # NOTE: we can guess the filename from the response headers
    #   Content-Disposition: inline; filename="some_file_name.ext"
    #   Content-Disposition: attachment; filename="some_file_name.ext"
    key = "Content-Disposition"
    if key in response.headers:
        msg = EmailMessage()
        msg[key] = response.headers[key]
        filename = msg.get_filename()

    key = "Content-Type"
    if not filename and key in response.headers:
        msg = EmailMessage()
        msg[key] = response.headers[key]

        from mimetypes import guess_extension

        ext = guess_extension(msg.get_content_type())

        result = urlsplit(response.url)
        # NOTE: a URL path is POSIX-style whatever the platform
        if result.path.strip("/"):
            basename = posixpath.basename(result.path)
        else:
            basename = result.netloc

        # NOTE: an unknown Content-Type gives no usable name: leave the
        # filename unset so that callers guess from the contents instead
        if ext is not None:
            filename = f"{basename}{ext}"

    return filename


def download_document(
    url: str,
    expected_document_extension: str | None = None,
    filename: str | None = None,
) -> str | None:
    """Download a document from *url* and store it in a local file.

    :param url: the URL of a remote file.
    :param expected_document_extension: an expected file extension.
    :param filename: a file name for the document.

    :returns: an absolute path to a local file containing the data from *url*.
    """
    if expected_document_extension is not None:
        expected_document_extension = expected_document_extension.lower().lstrip(".")

    response = _request(url)
    if response is None:
        return None

    return _store_response(response, expected_document_extension, filename)


def _store_response(
    response: requests.Response,
    expected_document_extension: str | None = None,
    filename: str | None = None,
) -> str | None:
    """Store the *response* as a local document file.

    :param response: the response to store.
    :param expected_document_extension: an expected file extension without leading dot.
    :param filename: a suggested file name.
    :returns: an absolute path to the stored file or ``None``.
    """
    from papis.filetype import guess_content_extension

    if expected_document_extension is not None and _is_html_response(response):
        logger.error(
            "Downloaded file from '%s' isn't of the expected type '%s'.",
            response.url,
            expected_document_extension,
        )
        return None

    if not filename:
        filename = get_filename_from_response(response)

    guessed_ext = guess_content_extension(response.content)
    _, file_ext = os.path.splitext(filename) if filename else ("", "")

    if expected_document_extension is not None:
        if guessed_ext is not None:
            matches = guessed_ext.lower() == expected_document_extension
        else:
            matches = (
                not file_ext
                or file_ext.lower().lstrip(".") == expected_document_extension
            )

        if not matches:
            logger.error(
                "Downloaded file from '%s' isn't of the expected type '%s'.",
                response.url,
                expected_document_extension,
            )
            return None

        ext = f".{expected_document_extension}"
    elif file_ext:
        ext = file_ext
    elif guessed_ext:
        ext = f".{guessed_ext}"
    else:
        ext = ""

    if filename:
        from papis.paths import make_unique_file

        stem = os.path.splitext(os.path.basename(filename))[0]
        outfile = make_unique_file(os.path.join(_TEMP_DIR.name, f"{stem}{ext}"))

        with open(outfile, mode="wb") as f:
            f.write(response.content)
    else:
        with tempfile.NamedTemporaryFile(
            mode="wb+", suffix=f"{ext}", delete=False, dir=_TEMP_DIR.name
        ) as f:
            f.write(response.content)
            outfile = f.name

    return outfile


def read_content(path: str) -> str | None:
    """Read the text content of the local file *path*.

    :param path: a local file path.
    :returns: the decoded UTF-8 text, or ``None`` if the file is not readable as text.
    """
    try:
        with open(path, encoding="utf-8") as fd:
            return fd.read()
    except UnicodeDecodeError as exc:
        logger.debug("Could not read file '%s' as text.", path, exc_info=exc)
    except OSError as exc:
        logger.warning("Could not read file '%s' as text.", path, exc_info=exc)

    return None


def _inspect_file(path: str) -> tuple[str | None, dict[str, str]]:
    """Inspect a local file for evidence.

    :param path: a local file path.
    :returns: the decoded UTF-8 text (or ``None``) and the extracted identifier fields.
    """
    return read_content(path), extract_fields(path)


def gather_file(item: str) -> GatheredItem:
    """Gather a local file."""
    content, fields = _inspect_file(item)
    return GatheredItem(
        evidence=LookupInput(input=item, kind="file", content=content, fields=fields),
        local_files=[item],
    )


def gather_url(item: str) -> GatheredItem | None:
    """Gather a URL.

    :returns: the gathered item, or ``None`` when nothing could be gathered.
    """
    response = _request(item)
    if response is None:
        return None

    if _is_html_response(response):
        return GatheredItem(
            evidence=LookupInput(
                input=item,
                kind="webpage",
                content=response.content.decode("utf-8", errors="replace"),
            )
        )

    logger.info("Downloading file from '%s'.", item)

    path = _store_response(response)
    if path is None:
        return None

    content, fields = _inspect_file(path)
    return GatheredItem(
        evidence=LookupInput(input=item, kind="file", content=content, fields=fields),
        local_files=[path],
    )


def gather_bare(item: str) -> GatheredItem:
    """Gather a bare string."""
    return GatheredItem(evidence=LookupInput(input=item))


def gather(item: str) -> GatheredItem:
    """Gather evidence for a single item user input.

    - **file path**: produces ``fields`` via extractors or ``content`` for metadata
      files.
    - **URL**: An HTML response is a web page. Anything else is downloaded and treated
      like a local file.
    - **bare string**: only ``evidence.input``.

    :param item: the user input.
    """
    item = item.strip()

    gathered: GatheredItem | None
    if os.path.isfile(item):
        gathered = gather_file(item)
    elif urlsplit(item).scheme.lower() in {"http", "https"}:
        gathered = gather_url(item)
        if gathered is None:
            gathered = gather_bare(item)
    else:
        gathered = gather_bare(item)

    return gathered
