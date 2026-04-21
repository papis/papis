"""Doctor check endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import Path, Query, Request

import papis.config
import papis.document
from papis.doctor import (
    REGISTERED_CHECKS,
    fix_errors,
    gather_errors,
    registered_checks_names,
)
from papis.id import ID_KEY_NAME
from papis.server import exceptions, git as server_git
from papis.server.models import (
    DoctorChecksResponse,
    DoctorError,
    DoctorNameResponse,
    DoctorResponse,
)
from papis.server.routes.libraries import get_db, library_router


@library_router.get(
    "/doctor",
    tags=["Doctor"],
    response_model=DoctorChecksResponse,
    responses=exceptions.ResourceNotFoundError.responses(
        codes=[exceptions.ErrorCode.LIBRARY_NOT_FOUND]
    ),
)
async def list_doctor_checks(
    library: Annotated[str, Path(description="Library name")],
) -> DoctorChecksResponse:
    """List all available doctor checks."""
    return DoctorChecksResponse(
        checks=[DoctorNameResponse(name=name) for name in registered_checks_names()]
    )


@library_router.post(
    "/doctor",
    tags=["Doctor"],
    response_model=DoctorResponse,
    responses={
        **exceptions.ResourceNotFoundError.responses(
            codes=[
                exceptions.ErrorCode.LIBRARY_NOT_FOUND,
                exceptions.ErrorCode.CHECK_NOT_FOUND,
            ]
        ),
        **exceptions.PreconditionFailedError.responses(
            codes=[exceptions.ErrorCode.NOT_A_GIT_REPOSITORY]
        ),
    },
)
async def run_doctor(
    request: Request,
    library: Annotated[str, Path(description="Library name")],
    checks: Annotated[
        list[str] | None,
        Query(
            description="Check names to run"
            " (uses the ``doctor-default-checks`` option if omitted)",
        ),
    ] = None,
    query: Annotated[
        str | None,
        Query(description="Papis query to limit which documents are checked"),
    ] = None,
    fix: Annotated[
        bool, Query(description="Apply auto-fixers for checks that offer them")
    ] = False,
    git: Annotated[
        bool | None,
        Query(
            description="Commit changes to git (uses the ``use-git`` option if omitted)"
        ),
    ] = None,
) -> DoctorResponse:
    """Run doctor checks on documents, optionally fixing errors.

    If ``checks`` is omitted, the configured ``doctor-default-checks`` are used.
    If ``query`` is omitted, all documents are checked.
    """
    db = get_db(library)
    lib_path = request.state.lib_path
    do_git = server_git.should_use_git(git, lib_path, root=lib_path)

    if checks is None:
        checks = papis.config.getlist("default-checks", section="doctor")
        checks.extend(papis.config.getlist("default-checks-extend", section="doctor"))

    unknown = [c for c in checks if c not in REGISTERED_CHECKS]
    if unknown:
        raise exceptions.ResourceNotFoundError(
            f"Unknown doctor check(s): {', '.join(unknown)}",
            code=exceptions.ErrorCode.CHECK_NOT_FOUND,
            context={"checks": unknown},
        )

    if query:
        docs = db.query(query)
    else:
        docs = db.get_all_documents()

    errors = gather_errors(docs, checks=checks)

    if fix:
        for doc in docs:
            fix_errors(doc, checks=checks)
            doc.save()
            db.update(doc)
            if do_git:
                folder = doc.get_main_folder()
                if folder:
                    server_git.add_and_commit(
                        folder,
                        papis.config.getstring("info-name"),
                        f"Fix doctor errors for '{papis.document.describe(doc)}'",
                    )

    results: dict[str, list[DoctorError]] = {}

    for doc in docs:
        error_doc_id = str(doc.get(ID_KEY_NAME, ""))
        results.setdefault(error_doc_id, [])

    for error in errors:
        error_doc = error.doc
        error_doc_id = (
            str(error_doc.get(ID_KEY_NAME, "")) if error_doc is not None else ""
        )
        results.setdefault(error_doc_id, []).append(
            DoctorError(
                name=error.name,
                message=error.msg,
                payload=error.payload,
                fix_available=error.fix_action is not None,
                fixed=fix and error.fix_action is not None,
            )
        )

    return DoctorResponse(results=results)
