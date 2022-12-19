from typing import Dict, Any


def query_path(libname: str) -> str:
    """
    Path for submiting queries.
    """
    return "/library/{libname}/query".format(libname=libname)


def fetch_citations_server_path(libname: str, doc: Dict[str, Any]) -> str:
    """
    Path for fetching citations for papers
    """
    if "ref" not in doc:
        return "#"
    return ("/library/{libname}/document/fetch-citations/ref:{ref}"
            .format(ref=doc["ref"], libname=libname))


def doc_server_path(libname: str, doc: Dict[str, Any]) -> str:
    """
    The server path for a document, it might change in the future
    """
    # TODO: probably we should quote the ref (and later unquote)?
    if "ref" not in doc:
        return "#"
    return "/library/{libname}/document/ref:{ref}".format(ref=doc["ref"],
                                                          libname=libname)


def file_server_path(localpath: str,
                     libfolder: str,
                     libname: str) -> str:
    """
    Path for associated files of documents
    """
    return ("/library/{libname}/file/{0}"
            .format(localpath.replace(libfolder + "/", ""),
                    libname=libname))
