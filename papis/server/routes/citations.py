"""Citation and cited-by endpoints."""

from __future__ import annotations

import pathlib
from typing import Annotated

from fastapi import Path, Query, Request

import papis.document
from papis.citations import (
    fetch_and_save_citations,
    fetch_and_save_cited_by_from_database,
    get_citations as _get_citations,
    get_citations_file,
    get_cited_by as _get_cited_by,
    get_cited_by_file,
)
from papis.server import exceptions, git as server_git
from papis.server.models import CitationResponse, CitationsResponse, CitedByResponse
from papis.server.routes.documents import get_doc, get_folder
from papis.server.routes.libraries import get_db, library_router


@library_router.get(
    "/documents/{id}/citations",
    tags=["Document Citations"],
    response_model=CitationsResponse,
    response_model_exclude_none=True,
    responses=exceptions.ResourceNotFoundError.responses(
        codes=[
            exceptions.ErrorCode.LIBRARY_NOT_FOUND,
            exceptions.ErrorCode.DOCUMENT_NOT_FOUND,
        ]
    ),
)
async def get_citations(
    library: Annotated[str, Path(description="Library name")],
    id: Annotated[str, Path(description="Document ID")],
) -> CitationsResponse:
    """Get a document's citations.

    Returns the contents of the ``citations.yaml`` file. If the file does
    not exist, returns an empty list.
    """
    db = get_db(library)
    doc = get_doc(db, id)

    return CitationsResponse(
        citations=[CitationResponse(**item) for item in _get_citations(doc)]
    )


@library_router.post(
    "/documents/{id}/citations",
    tags=["Document Citations"],
    response_model=CitationsResponse,
    response_model_exclude_none=True,
    responses={
        **exceptions.ResourceNotFoundError.responses(
            codes=[
                exceptions.ErrorCode.LIBRARY_NOT_FOUND,
                exceptions.ErrorCode.DOCUMENT_NOT_FOUND,
            ]
        ),
        **exceptions.BadRequestError.responses(
            codes=[
                exceptions.ErrorCode.CITATION_NO_DOI,
                exceptions.ErrorCode.CITATION_FETCH_EMPTY,
            ]
        ),
        **exceptions.PreconditionFailedError.responses(
            codes=[exceptions.ErrorCode.NOT_A_GIT_REPOSITORY]
        ),
    },
)
async def fetch_citations(
    request: Request,
    library: Annotated[str, Path(description="Library name")],
    id: Annotated[str, Path(description="Document ID")],
    git: Annotated[
        bool | None,
        Query(
            description="Commit changes to git (uses the ``use-git`` option if omitted)"
        ),
    ] = None,
) -> CitationsResponse:
    """Fetch and save citations for a document.

    Retrieves the document's reference list from Crossref using its DOI.
    If the cited paper exists locally, its full metadata is used. Otherwise, the
    reference is fetched from Crossref. The result is saved to ``citations.yaml``,
    overwriting any existing file.
    """
    db = get_db(library)
    doc = get_doc(db, id)
    doc_folder = get_folder(doc)
    do_git = server_git.should_use_git(git, doc_folder, root=request.state.lib_path)

    if not doc.get("doi"):
        raise exceptions.BadRequestError(
            "Document has no DOI. Citations can only be fetched for"
            " documents with a DOI.",
            code=exceptions.ErrorCode.CITATION_NO_DOI,
            context={"id": id},
        )

    try:
        fetch_and_save_citations(doc)
    except ValueError as exc:
        raise exceptions.BadRequestError(
            str(exc),
            code=exceptions.ErrorCode.CITATION_FETCH_EMPTY,
            context={"id": id},
        ) from exc

    if do_git:
        server_git.add_and_commit(
            doc_folder,
            "citations.yaml",
            f"Fetch citations for '{papis.document.describe(doc)}'",
        )

    return CitationsResponse(
        citations=[CitationResponse(**item) for item in _get_citations(doc)]
    )


@library_router.delete(
    "/documents/{id}/citations",
    status_code=204,
    tags=["Document Citations"],
    responses=exceptions.ResourceNotFoundError.responses(
        codes=[
            exceptions.ErrorCode.LIBRARY_NOT_FOUND,
            exceptions.ErrorCode.DOCUMENT_NOT_FOUND,
        ]
    )
    | exceptions.PreconditionFailedError.responses(
        codes=[exceptions.ErrorCode.NOT_A_GIT_REPOSITORY]
    ),
)
async def delete_citations(
    request: Request,
    library: Annotated[str, Path(description="Library name")],
    id: Annotated[str, Path(description="Document ID")],
    git: Annotated[
        bool | None,
        Query(
            description="Commit changes to git (uses the ``use-git`` option if omitted)"
        ),
    ] = None,
) -> None:
    """Delete a document's citations file."""
    db = get_db(library)
    doc = get_doc(db, id)
    doc_folder = get_folder(doc)
    do_git = server_git.should_use_git(git, doc_folder, root=request.state.lib_path)

    path = get_citations_file(doc)
    if not path:
        return

    pathlib.Path(path).unlink(missing_ok=True)

    if do_git:
        server_git.rm_cached(doc_folder, pathlib.Path(path).name)
        server_git.commit(
            doc_folder,
            f"Remove citations for '{papis.document.describe(doc)}'",
        )


@library_router.get(
    "/documents/{id}/cited-by",
    tags=["Document Citations"],
    response_model=CitedByResponse,
    response_model_exclude_none=True,
    responses=exceptions.ResourceNotFoundError.responses(
        codes=[
            exceptions.ErrorCode.LIBRARY_NOT_FOUND,
            exceptions.ErrorCode.DOCUMENT_NOT_FOUND,
        ]
    ),
)
async def get_cited_by(
    library: Annotated[str, Path(description="Library name")],
    id: Annotated[str, Path(description="Document ID")],
) -> CitedByResponse:
    """Get documents in the library that cite this document.

    Returns the contents of the ``cited-by.yaml`` file. If the file does
    not exist, returns an empty list.
    """
    db = get_db(library)
    doc = get_doc(db, id)

    return CitedByResponse(
        cited_by=[CitationResponse(**item) for item in _get_cited_by(doc)]
    )


@library_router.post(
    "/documents/{id}/cited-by",
    tags=["Document Citations"],
    response_model=CitedByResponse,
    response_model_exclude_none=True,
    responses=exceptions.ResourceNotFoundError.responses(
        codes=[
            exceptions.ErrorCode.LIBRARY_NOT_FOUND,
            exceptions.ErrorCode.DOCUMENT_NOT_FOUND,
        ]
    )
    | exceptions.PreconditionFailedError.responses(
        codes=[exceptions.ErrorCode.NOT_A_GIT_REPOSITORY]
    ),
)
async def fetch_cited_by(
    request: Request,
    library: Annotated[str, Path(description="Library name")],
    id: Annotated[str, Path(description="Document ID")],
    git: Annotated[
        bool | None,
        Query(
            description="Commit changes to git (uses the ``use-git`` option if omitted)"
        ),
    ] = None,
) -> CitedByResponse:
    """Fetch and save cited-by references for a document.

    Scans the local library for documents whose citations include this
    document's DOI. Saves the result to ``cited-by.yaml``.
    Always overwrites when the file already exists.
    """
    db = get_db(library)
    doc = get_doc(db, id)
    doc_folder = get_folder(doc)
    do_git = server_git.should_use_git(git, doc_folder, root=request.state.lib_path)

    fetch_and_save_cited_by_from_database(doc)

    if do_git:
        server_git.add_and_commit(
            doc_folder,
            "cited-by.yaml",
            f"Fetch cited-by for '{papis.document.describe(doc)}'",
        )

    return CitedByResponse(
        cited_by=[CitationResponse(**item) for item in _get_cited_by(doc)]
    )


@library_router.delete(
    "/documents/{id}/cited-by",
    status_code=204,
    tags=["Document Citations"],
    responses=exceptions.ResourceNotFoundError.responses(
        codes=[
            exceptions.ErrorCode.LIBRARY_NOT_FOUND,
            exceptions.ErrorCode.DOCUMENT_NOT_FOUND,
        ]
    )
    | exceptions.PreconditionFailedError.responses(
        codes=[exceptions.ErrorCode.NOT_A_GIT_REPOSITORY]
    ),
)
async def delete_cited_by(
    request: Request,
    library: Annotated[str, Path(description="Library name")],
    id: Annotated[str, Path(description="Document ID")],
    git: Annotated[
        bool | None,
        Query(
            description="Commit changes to git (uses the ``use-git`` option if omitted)"
        ),
    ] = None,
) -> None:
    """Delete a document's cited-by file."""
    db = get_db(library)
    doc = get_doc(db, id)
    doc_folder = get_folder(doc)
    do_git = server_git.should_use_git(git, doc_folder, root=request.state.lib_path)

    path = get_cited_by_file(doc)
    if not path:
        return

    pathlib.Path(path).unlink(missing_ok=True)

    if do_git:
        server_git.rm_cached(doc_folder, pathlib.Path(path).name)
        server_git.commit(
            doc_folder,
            f"Remove cited-by for '{papis.document.describe(doc)}'",
        )
