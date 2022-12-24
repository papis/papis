from typing import Dict, Any, Optional

import papis.id


def _ref(doc: Dict[str, Any]) -> Optional[str]:
    if papis.id.has_id(doc):
        return papis.id.get(doc)
    return None


def format_if_has_id(doc: Dict[str, Any],
                     fmt: str,
                     *args: Any,
                     **kwargs: Any) -> str:
    """
    Formats the string *fmt* only if *doc* has the ``papis_id`` key, since the
    path requires it.
    """
    if papis.id.has_id(doc):
        return fmt.format(*args, **kwargs)
    return ""


def query_path(libname: str) -> str:
    """
    Path for submiting queries.
    """
    return "/library/{libname}/query".format(libname=libname)


def fetch_citations_server_path(libname: str, doc: Dict[str, Any]) -> str:
    """
    Path for fetching citations for papers.
    """
    return format_if_has_id(doc,
                            "/library/{libname}/document/"
                            "fetch-citations/{ref}",
                            ref=_ref(doc),
                            libname=libname)


def fetch_cited_by_server_path(libname: str, doc: Dict[str, Any]) -> str:
    """
    Path for fetching cited-by type citations for papers
    """
    return format_if_has_id(doc,
                            "/library/{libname}/document/"
                            "fetch-cited-by/{ref}",
                            ref=_ref(doc),
                            libname=libname)


def update_notes(libname: str, doc: Dict[str, Any]) -> str:
    """
    Path for updating the notes of the paper.
    """
    return format_if_has_id(doc,
                            "/library/{libname}/document/notes/{ref}",
                            ref=_ref(doc),
                            libname=libname)


def update_info(libname: str, doc: Dict[str, Any]) -> str:
    """
    Path for updating the ``info.yaml`` file itself.
    """
    return format_if_has_id(doc,
                            "/library/{libname}/document/info/{ref}",
                            ref=_ref(doc),
                            libname=libname)


def doc_server_path(libname: str, doc: Dict[str, Any]) -> str:
    """
    The server path for a document (it might change in the future).
    """
    return format_if_has_id(doc,
                            "/library/{libname}/document/{ref}",
                            ref=_ref(doc),
                            libname=libname)


def file_server_path(localpath: str,
                     libfolder: str,
                     libname: str) -> str:
    """
    Path for associated files of documents.
    """
    return ("/library/{libname}/file/{0}"
            .format(localpath.replace(libfolder + "/", ""),
                    libname=libname))
