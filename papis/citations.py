import os
from typing import Dict, Any, List, Optional, Sequence, Tuple

import tqdm
import colorama

import papis.config
import papis.database
import papis.crossref
import papis.yaml
import papis.utils
import papis.logging
import papis.document

logger = papis.logging.get_logger(__name__)

#: A citation for an existing document.
Citation = Dict[str, Any]
#: A list of citations for an existing document.
Citations = List[Citation]


def _delete_citations_key(citations: Citations) -> None:
    for data in citations:
        if "citations" in data:
            del data["citations"]


# =============================================================================
# CITATIONS FUNCTIONS
# =============================================================================


def get_metadata_citations(doc: papis.document.DocumentLike) -> Citations:
    """Get the citations in the metadata that contain a DOI."""
    return [cit for cit in doc.get("citations", [])
            if isinstance(cit, dict) and "doi" in cit]


def fetch_citations(doc: papis.document.Document) -> Citations:
    """Retrieve citations for the document.

    Citation retrieval is mainly based on querying Crossref metadata based on the
    DOI of the document. If the document does not have a DOI, this function will
    fail to retrieve any citations.

    :returns: a list of citations that have a DOI.
    """

    metadata_citations = get_metadata_citations(doc)
    if not metadata_citations:
        doi = doc.get("doi")
        if doi:
            logger.debug("Trying fetching citations with DOI '%s'.", doi)

            data = papis.crossref.doi_to_data(doi)
            metadata_citations = get_metadata_citations(data)

            if not metadata_citations:
                raise ValueError(
                    "Could not retrieve citations from the DOI '{}' for document '{}'"
                    .format(doi, papis.document.describe(doc)))
        else:
            raise ValueError(
                "Cannot find citations in a document without a DOI: '{}'"
                .format(papis.document.describe(doc)))

    dois = [str(d.get("doi")).lower() for d in metadata_citations if "doi" in d]
    logger.info("Found %d citations with a DOI.", len(dois))

    logger.info("Checking which citations are already in the library.")
    dois_with_data = get_citations_from_database(dois)

    for data in dois_with_data:
        doi = data.get("doi", "").lower()
        if doi:
            dois.remove(doi)

    logger.info("Found %d citations in library.", len(dois_with_data))
    logger.info("Fetching %d citations from Crossref.", len(dois))

    with tqdm.tqdm(iterable=dois) as progress:
        for doi in progress:
            crossref_data = papis.crossref.get_data(dois=[doi])
            progress.set_description("{c.Fore.GREEN}{c.Back.BLACK}"
                                     "{0: <22.22}{c.Style.RESET_ALL}"
                                     .format(doi, c=colorama))
            if crossref_data:
                dois_with_data.extend(crossref_data)

    _delete_citations_key(dois_with_data)
    return dois_with_data


def get_citations_from_database(dois: Sequence[str]) -> Citations:
    """Look for document DOIs in the database.

    :param dois: a sequence of DOIs to look for in the current library database.
    :returns: a sequence of documents from the current library that match the
        given *dois*, if any.
    """
    db = papis.database.get()

    dois_with_data: List[Dict[str, Any]] = []
    with tqdm.tqdm(iterable=dois) as progress:
        for doi in progress:
            citation = db.query_dict({"doi": doi})

            if citation:
                progress.set_description("{c.Fore.GREEN}{c.Back.BLACK}"
                                         "{0: <22.22}"
                                         "{c.Style.RESET_ALL}"
                                         .format(doi, c=colorama))
                data = papis.document.to_dict(citation[0])
                dois_with_data.append(data)
            else:
                progress.set_description("{c.Fore.RED}{c.Back.BLACK}"
                                         "{0: <22.22}{c.Style.RESET_ALL}"
                                         .format(doi, c=colorama))

    return dois_with_data


def update_and_save_citations_from_database_from_doc(
        doc: papis.document.Document) -> None:
    """Update the citations file of an existing document.

    This function will get any existing citations in the document, update them
    as appropriate and save them back to the citation file.
    """
    citations = get_citations(doc)
    new_citations = update_citations_from_database(citations)
    save_citations(doc, new_citations)


def update_citations_from_database(citations: Citations) -> Citations:
    """Update a list of citations with data from the database.

    :param citations: a list of existing citations to update.
    """
    new_citations: List[Dict[str, Any]] = []
    dois = [str(c.get("doi")).lower() for c in citations
            if "doi" in c]

    new_data_list = get_citations_from_database(dois)
    for data in new_data_list:
        doi = data.get("doi", "").lower()
        if doi:
            dois.remove(doi)

    new_citations.extend(new_data_list)
    for citation in citations:
        doi = citation.get("doi")
        if doi and doi not in dois:
            continue
        new_citations.append(citation)

    _delete_citations_key(new_citations)
    return new_citations


def save_citations(doc: papis.document.Document, citations: Citations) -> None:
    """Save the *citations* to the document's citation file."""

    file_path = get_citations_file(doc)
    if not file_path:
        return

    papis.yaml.list_to_path(citations, file_path)


def fetch_and_save_citations(doc: papis.document.Document) -> None:
    """Retrieve citations from available sources and save them to the citations file."""
    citations = fetch_citations(doc)
    if citations:
        save_citations(doc, citations)


def get_citations_file(doc: papis.document.Document) -> Optional[str]:
    """Get the document's citation file path (see
    :ref:`config-settings-citations-file-name`).

    :returns: an absolute path to the citations file for *doc*.
    """
    folder = doc.get_main_folder()
    file_name = papis.config.getstring("citations-file-name")
    if not folder:
        return None

    return os.path.join(folder, file_name)


def has_citations(doc: papis.document.Document) -> bool:
    """
    :returns: *True* if the document has an existing citations file and *False*
        otherwise.
    """
    file_path = get_citations_file(doc)
    if not file_path:
        return False

    return os.path.exists(file_path)


def get_citations(doc: papis.document.Document) -> Citations:
    """Retrieve citations from the document's citation file."""

    if has_citations(doc):
        file_path = get_citations_file(doc)
        if not file_path:
            return []

        return papis.yaml.yaml_to_list(file_path)

    return []


# =============================================================================
# CITED BY FUNCTIONS
# =============================================================================


def get_cited_by_file(doc: papis.document.Document) -> Optional[str]:
    """Get the documents cited-by file (see :ref:`config-settings-cited-by-file-name`).

    :returns: an absolute path to the cited-by file for *doc*.
    """

    folder = doc.get_main_folder()
    file_name = papis.config.getstring("cited-by-file-name")
    if not folder:
        return None

    return os.path.join(folder, file_name)


def has_cited_by(doc: papis.document.Document) -> bool:
    """
    :returns: *True* if the document has a cited-by file and *False* otherwise.
    """
    file_path = get_cited_by_file(doc)
    if not file_path:
        return False
    return os.path.exists(file_path)


def save_cited_by(doc: papis.document.Document, citations: Citations) -> None:
    """Save the cited-by list *citations* to the document's cited-by file."""
    file_path = get_citations_file(doc)
    if not file_path:
        return

    papis.yaml.list_to_path(citations, file_path)


def _cites_me_p(doi_doc: Tuple[str, papis.document.Document]) -> Optional[Citation]:
    doi, doc = doi_doc
    if not has_citations(doc):
        return None

    citations = get_citations(doc)
    found = [c for c in citations
             if c.get("doi", "").lower() == doi]
    if found:
        return papis.document.to_dict(doc)

    return None


def fetch_cited_by_from_database(cit: Citation) -> Citations:
    """Fetch a list of documents that cite *cit* from the database.

    :param cit: a citation to look for in the database.
    :returns: a list of documents that cite *cit*.
    """
    doi = str(cit.get("doi", "")).lower()
    if not doi:
        return []

    result: List[Citation] = []
    db = papis.database.get()
    documents = db.get_all_documents()

    # NOTE: using parmap makes it around 2.5x faster with an ssd
    # in a 2k documents library
    result = [d for d in papis.utils.parmap(_cites_me_p,
                                            [(doi, x) for x in documents])
              if d is not None]

    _delete_citations_key(result)
    return result


def fetch_and_save_cited_by_from_database(doc: papis.document.Document) -> None:
    """Call :func:`fetch_cited_by_from_database` and :func:`save_cited_by`."""
    citations = fetch_cited_by_from_database(doc)

    file_path = get_cited_by_file(doc)
    if citations and file_path:
        papis.yaml.list_to_path(citations, file_path)


def get_cited_by(doc: papis.document.Document) -> Citations:
    """Get cited-by citations for the given document."""

    if has_cited_by(doc):
        file_path = get_cited_by_file(doc)
        if not file_path:
            return []

        return papis.yaml.yaml_to_list(file_path)

    return []
