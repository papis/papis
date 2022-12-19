from typing import Dict, Any, List, Optional, Sequence
import logging
import os

import tqdm
import colorama

import papis.config
import papis.database
import papis.crossref
import papis.yaml
from papis.document import Document, to_dict


LOGGER = logging.getLogger("citations")


def get_metadata_citations(doc: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Get the citations in the metadata that contains a doi.
    """
    return [cit for cit in doc.get("citations", [])
            if isinstance(cit, dict) and "doi" in cit]


def fetch_citations(doc: Document) -> List[Dict[str, Any]]:
    metadata_citations = get_metadata_citations(doc)
    if not metadata_citations:
        if doc.has("doi"):
            LOGGER.debug("trying with doi '%s'", doc["doi"])
            data = papis.crossref.doi_to_data(doc["doi"])
            metadata_citations = get_metadata_citations(data)
            if not metadata_citations:
                raise ValueError("We could not retrieve citations from the doi"
                                 " '{}'".format(doc["doi"]))
        else:
            raise ValueError("No possible finding citations "
                             "in '{}' due to lack of doi "
                             .format(doc))

    dois = [d.get("doi") for d in metadata_citations]
    LOGGER.info("%d citations found to query", len(dois))

    dois_with_data = [
    ]  # type: List[Dict[str, Any]]
    found_in_lib_dois = [
    ]  # type: List[Dict[str, Any]]
    db = papis.database.get()

    LOGGER.info("Checking which citations are already in the library")
    with tqdm.tqdm(iterable=dois) as progress:
        for doi in progress:
            citation = db.query_dict({"doi": doi})
            if citation:
                progress.set_description("{c.Fore.GREEN}{c.Back.BLACK}"
                                         "{0: <22.22}"
                                         "{c.Style.RESET_ALL}"
                                         .format(doi, c=colorama))
                data = to_dict(citation[0])
                dois_with_data.append(data)
                found_in_lib_dois.append(doi)
            else:
                progress.set_description("{c.Fore.RED}{c.Back.BLACK}"
                                         "{0: <22.22}{c.Style.RESET_ALL}"
                                         .format(doi, c=colorama))

    for doi in found_in_lib_dois:
        dois.remove(doi)

    LOGGER.info("Found %d DOIs in library", len(found_in_lib_dois))
    LOGGER.info("Fetching %d citations from crossref", len(dois))

    with tqdm.tqdm(iterable=dois) as progress:
        for doi in progress:
            _data = papis.crossref.get_data(dois=[doi])
            progress.set_description("{c.Fore.GREEN}{c.Back.BLACK}"
                                     "{0: <22.22}{c.Style.RESET_ALL}"
                                     .format(doi, c=colorama))
            if _data:
                dois_with_data.extend(_data)

    return dois_with_data


def fetch_and_save_citations(doc: Document) -> None:
    file_path = get_citations_file(doc)
    if not file_path:
        return
    citations = fetch_citations(doc)
    if citations:
        papis.yaml.list_to_path(citations, file_path)


def get_citations_file(doc: Document) -> Optional[str]:
    folder = doc.get_main_folder()
    file_name = papis.config.getstring("citations-file-name")
    if not folder:
        return None
    return os.path.join(folder, file_name)


def has_citations(doc: Document) -> bool:
    file_path = get_citations_file(doc)
    if not file_path:
        return False
    return os.path.exists(file_path)


def get_citations(doc: Document) -> Sequence[Dict[str, Any]]:
    if has_citations(doc):
        file_path = get_citations_file(doc)
        if not file_path:
            return []
        return papis.yaml.yaml_to_list(file_path)
    return []
