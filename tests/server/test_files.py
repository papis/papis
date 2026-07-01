from __future__ import annotations

import os
from io import BytesIO
from typing import TYPE_CHECKING

from fastapi.testclient import TestClient

if TYPE_CHECKING:
    from papis.testing import TemporaryConfiguration


def create_test_document(
    client: TestClient,
    path: str = "test-files-doc",
    title: str = "Test Document for Files",
) -> tuple[str, str]:
    """Create a test document and return (papis_id, path)."""
    response = client.post(
        "/api/v1/libraries/test/documents",
        json={"title": title},
        params={"folder": path},
    )
    assert response.status_code == 201
    return response.json()["papis_id"], path


# =============================================================================
# GET /libraries/{library}/documents/{id}/files
# =============================================================================


def test_list_files_empty(tmp_config: TemporaryConfiguration) -> None:
    """GET .../files returns empty list for document with no files."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, _ = create_test_document(client)

    response = client.get(f"/api/v1/libraries/test/documents/{papis_id}/files")

    assert response.status_code == 200
    data = response.json()
    assert data == []


def test_list_files(tmp_config: TemporaryConfiguration) -> None:
    """GET .../files returns list of files in document."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, _ = create_test_document(client)

    response1 = client.post(
        f"/api/v1/libraries/test/documents/{papis_id}/files",
        files={"upload": ("file1.pdf", BytesIO(b"Content 1"), "application/pdf")},
    )
    assert response1.status_code == 201
    response2 = client.post(
        f"/api/v1/libraries/test/documents/{papis_id}/files",
        files={"upload": ("file2.pdf", BytesIO(b"Content 2"), "application/pdf")},
    )
    assert response2.status_code == 201

    list_response = client.get(f"/api/v1/libraries/test/documents/{papis_id}/files")
    files = list_response.json()
    assert "file1.pdf" in files
    assert "file2.pdf" in files


# =============================================================================
# POST /libraries/{library}/documents/{id}/files
# =============================================================================


def test_add_file(tmp_config: TemporaryConfiguration) -> None:
    """POST .../files adds a file to a document."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, path = create_test_document(client)

    file_content = b"Test file content"
    response = client.post(
        f"/api/v1/libraries/test/documents/{papis_id}/files",
        files={"upload": ("test.pdf", BytesIO(file_content), "application/pdf")},
    )

    assert response.status_code == 201

    list_response = client.get(f"/api/v1/libraries/test/documents/{papis_id}/files")
    assert list_response.status_code == 200
    assert "test.pdf" in list_response.json()

    # Verify on disk
    file_path = os.path.join(tmp_config.libdir, path, "test.pdf")
    assert os.path.exists(file_path)
    assert open(file_path, "rb").read() == file_content


def test_add_file_path_normalization(tmp_config: TemporaryConfiguration) -> None:
    """POST .../files normalizes special characters to safe filenames."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, _ = create_test_document(client)

    response = client.post(
        f"/api/v1/libraries/test/documents/{papis_id}/files",
        files={
            "upload": (
                "test!!file<>with/special*chars.pdf",
                BytesIO(b"Test content"),
                "application/pdf",
            )
        },
    )
    assert response.status_code == 201

    # Verify on disk
    list_response = client.get(f"/api/v1/libraries/test/documents/{papis_id}/files")
    files = list_response.json()
    assert files == ["test-file-with-special-chars.pdf"]


def test_add_file_unique_name_suffix(tmp_config: TemporaryConfiguration) -> None:
    """POST .../files adds suffix to avoid filename clashes."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, _ = create_test_document(client)

    response1 = client.post(
        f"/api/v1/libraries/test/documents/{papis_id}/files",
        files={"upload": ("document.pdf", BytesIO(b"Content 1"), "application/pdf")},
    )
    assert response1.status_code == 201
    assert response1.json() == "document.pdf"

    response2 = client.post(
        f"/api/v1/libraries/test/documents/{papis_id}/files",
        files={"upload": ("document.pdf", BytesIO(b"Content 2"), "application/pdf")},
    )
    assert response2.status_code == 201
    assert response2.json() == "document-a.pdf"


def test_add_file_unique_name_suffix_non_file(
    tmp_config: TemporaryConfiguration,
) -> None:
    """POST .../files adds suffix when a note with the same name exists."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, _ = create_test_document(client)

    client.post(
        f"/api/v1/libraries/test/documents/{papis_id}/notes",
        files={"upload": ("mydoc.md", BytesIO(b"Note content"), "text/markdown")},
    )

    response = client.post(
        f"/api/v1/libraries/test/documents/{papis_id}/files",
        files={"upload": ("mydoc.md", BytesIO(b"File content"), "text/markdown")},
    )

    assert response.status_code == 201
    assert response.json() == "mydoc-a.md"


def test_document_not_found(tmp_config: TemporaryConfiguration) -> None:
    """POST .../files returns 404 for non-existent document."""
    from papis.server.app import app

    client = TestClient(app)

    response = client.get("/api/v1/libraries/test/documents/nonexistent-id/files")
    assert response.status_code == 404

    response = client.post(
        "/api/v1/libraries/test/documents/nonexistent-id/files",
        files={"upload": ("test.pdf", BytesIO(b"Content"), "application/pdf")},
    )
    assert response.status_code == 404


# =============================================================================
# GET /libraries/{library}/documents/{id}/files/{file}
# =============================================================================


def test_download_file(tmp_config: TemporaryConfiguration) -> None:
    """GET .../files/{file} downloads a file."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, _ = create_test_document(client)

    file_content = b"Download test content"
    client.post(
        f"/api/v1/libraries/test/documents/{papis_id}/files",
        files={"upload": ("download.pdf", BytesIO(file_content), "application/pdf")},
    )

    response = client.get(
        f"/api/v1/libraries/test/documents/{papis_id}/files/download.pdf"
    )

    assert response.status_code == 200
    assert response.content == file_content


def test_download_file_not_found(tmp_config: TemporaryConfiguration) -> None:
    """GET .../files/{file} returns 404 for non-existent file."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, _ = create_test_document(client)

    response = client.get(
        f"/api/v1/libraries/test/documents/{papis_id}/files/nonexistent.pdf"
    )

    assert response.status_code == 404


def test_download_file_with_special_chars(tmp_config: TemporaryConfiguration) -> None:
    """GET .../files/{file} can download a file with special characters in name."""
    from papis.document import Document
    from papis.server.app import app
    from papis.server.routes.documents import get_db

    client = TestClient(app)
    papis_id, doc_path = create_test_document(
        client, path="special-chars-test", title="Special Chars File Test"
    )

    special_filename = "test<>file.pdf"
    with open(
        os.path.join(tmp_config.libdir, doc_path, special_filename),
        "w",
        encoding="utf-8",
    ) as f:
        f.write("content")
    doc = Document(folder=os.path.join(tmp_config.libdir, doc_path))
    doc["files"] = [special_filename]
    doc.save()
    get_db("test").update(doc)

    response = client.get(
        f"/api/v1/libraries/test/documents/{papis_id}/files/{special_filename}"
    )
    assert response.status_code == 200
    assert response.content == b"content"


# =============================================================================
# PUT /libraries/{library}/documents/{id}/files/{file}
# =============================================================================


def test_replace_file(tmp_config: TemporaryConfiguration) -> None:
    """PUT .../files/{file} replaces file content."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, _ = create_test_document(client)

    client.post(
        f"/api/v1/libraries/test/documents/{papis_id}/files",
        files={
            "upload": ("original.pdf", BytesIO(b"Original content"), "application/pdf")
        },
    )

    new_content = b"Replaced content"
    response = client.put(
        f"/api/v1/libraries/test/documents/{papis_id}/files/original.pdf",
        files={"upload": ("original.pdf", BytesIO(new_content), "application/pdf")},
    )

    assert response.status_code == 200
    assert response.json() == "original.pdf"

    download = client.get(
        f"/api/v1/libraries/test/documents/{papis_id}/files/original.pdf"
    )
    assert download.content == new_content


def test_replace_file_not_found(tmp_config: TemporaryConfiguration) -> None:
    """PUT .../files/{file} returns 404 for non-existent file."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, _ = create_test_document(client)

    response = client.put(
        f"/api/v1/libraries/test/documents/{papis_id}/files/nonexistent.pdf",
        files={"upload": ("nonexistent.pdf", BytesIO(b"Content"), "application/pdf")},
    )

    assert response.status_code == 404


def test_replace_file_with_special_chars(tmp_config: TemporaryConfiguration) -> None:
    """PUT .../files/{file} can replace a file with special characters in name."""
    from papis.document import Document
    from papis.server.app import app
    from papis.server.routes.documents import get_db

    client = TestClient(app)
    papis_id, doc_path = create_test_document(
        client, path="special-chars-test", title="Special Chars File Test"
    )

    special_filename = "test<>file.pdf"
    with open(
        os.path.join(tmp_config.libdir, doc_path, special_filename),
        "w",
        encoding="utf-8",
    ) as f:
        f.write("content")

    doc = Document(folder=os.path.join(tmp_config.libdir, doc_path))
    doc["files"] = [special_filename]
    doc.save()
    get_db("test").update(doc)

    response = client.put(
        f"/api/v1/libraries/test/documents/{papis_id}/files/{special_filename}",
        files={
            "upload": (special_filename, BytesIO(b"new content"), "application/pdf")
        },
    )
    assert response.status_code == 200
    assert response.json() == special_filename


# =============================================================================
# DELETE /libraries/{library}/documents/{id}/files/{file}
# =============================================================================


def test_delete_file(tmp_config: TemporaryConfiguration) -> None:
    """DELETE .../files/{file} removes a file from document."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, path = create_test_document(client)

    client.post(
        f"/api/v1/libraries/test/documents/{papis_id}/files",
        files={"upload": ("todelete.pdf", BytesIO(b"To delete"), "application/pdf")},
    )

    response = client.delete(
        f"/api/v1/libraries/test/documents/{papis_id}/files/todelete.pdf"
    )

    assert response.status_code == 204

    list_response = client.get(f"/api/v1/libraries/test/documents/{papis_id}/files")
    assert "todelete.pdf" not in list_response.json()

    # Verify on disk
    file_path = os.path.join(tmp_config.libdir, path, "todelete.pdf")
    assert not os.path.exists(file_path), "File should be deleted from disk"


def test_delete_file_not_found(tmp_config: TemporaryConfiguration) -> None:
    """DELETE .../files/{file} returns 404 for non-existent file."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, _ = create_test_document(client)

    response = client.delete(
        f"/api/v1/libraries/test/documents/{papis_id}/files/nonexistent.pdf"
    )

    assert response.status_code == 404


def test_delete_file_with_special_chars(tmp_config: TemporaryConfiguration) -> None:
    """DELETE .../files/{file} can delete a file with special characters in name."""
    from papis.document import Document
    from papis.server.app import app
    from papis.server.routes.documents import get_db

    client = TestClient(app)
    papis_id, doc_path = create_test_document(
        client, path="special-chars-test", title="Special Chars File Test"
    )

    special_filename = "test<>file.pdf"
    with open(
        os.path.join(tmp_config.libdir, doc_path, special_filename),
        "w",
        encoding="utf-8",
    ) as f:
        f.write("content")

    doc = Document(folder=os.path.join(tmp_config.libdir, doc_path))
    doc["files"] = [special_filename]
    doc.save()
    get_db("test").update(doc)

    response = client.delete(
        f"/api/v1/libraries/test/documents/{papis_id}/files/{special_filename}"
    )
    assert response.status_code == 204
    assert client.get(f"/api/v1/libraries/test/documents/{papis_id}/files").json() == []


# =============================================================================
# PATCH /libraries/{library}/documents/{id}/files
# =============================================================================


def test_rename_file(tmp_config: TemporaryConfiguration) -> None:
    """PATCH .../files renames a file."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, path = create_test_document(client)

    client.post(
        f"/api/v1/libraries/test/documents/{papis_id}/files",
        files={"upload": ("oldname.pdf", BytesIO(b"Content"), "application/pdf")},
    )

    response = client.patch(
        f"/api/v1/libraries/test/documents/{papis_id}/files",
        params={"old_file": "oldname.pdf", "new_file": "newname.pdf"},
    )

    assert response.status_code == 200
    assert response.json() == "newname.pdf"

    list_response = client.get(f"/api/v1/libraries/test/documents/{papis_id}/files")
    files = list_response.json()
    assert "newname.pdf" in files
    assert "oldname.pdf" not in files

    # Verify on disk
    old_file = os.path.join(tmp_config.libdir, path, "oldname.pdf")
    new_file = os.path.join(tmp_config.libdir, path, "newname.pdf")
    assert os.path.exists(new_file)
    assert not os.path.exists(old_file)


def test_rename_file_not_found(tmp_config: TemporaryConfiguration) -> None:
    """PATCH .../files returns 404 when old file not in document."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, _ = create_test_document(client)

    response = client.patch(
        f"/api/v1/libraries/test/documents/{papis_id}/files",
        params={"old_file": "nonexistent.pdf", "new_file": "new.pdf"},
    )

    assert response.status_code == 404


def test_rename_file_path_normalization(tmp_config: TemporaryConfiguration) -> None:
    """PATCH .../files normalizes special characters in new filename."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, path = create_test_document(client)

    client.post(
        f"/api/v1/libraries/test/documents/{papis_id}/files",
        files={"upload": ("oldname.pdf", BytesIO(b"Content"), "application/pdf")},
    )

    response = client.patch(
        f"/api/v1/libraries/test/documents/{papis_id}/files",
        params={
            "old_file": "oldname.pdf",
            "new_file": "new!!name<>with/special*chars.pdf",
        },
    )
    assert response.status_code == 200

    list_response = client.get(f"/api/v1/libraries/test/documents/{papis_id}/files")
    files = list_response.json()
    assert files == ["new-name-with-special-chars.pdf"]

    # Verify on disk
    old_file = os.path.join(tmp_config.libdir, path, "oldname.pdf")
    new_file = os.path.join(tmp_config.libdir, path, "new-name-with-special-chars.pdf")
    assert os.path.exists(new_file), "New file should exist on disk"
    assert not os.path.exists(old_file), "Old file should be renamed (deleted)"


def test_rename_file_unique_name_suffix(tmp_config: TemporaryConfiguration) -> None:
    """PATCH .../files adds suffix to avoid filename clashes."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, _ = create_test_document(client)

    client.post(
        f"/api/v1/libraries/test/documents/{papis_id}/files",
        files={"upload": ("file1.pdf", BytesIO(b"Content 1"), "application/pdf")},
    )
    client.post(
        f"/api/v1/libraries/test/documents/{papis_id}/files",
        files={"upload": ("file2.pdf", BytesIO(b"Content 2"), "application/pdf")},
    )

    response = client.patch(
        f"/api/v1/libraries/test/documents/{papis_id}/files",
        params={"old_file": "file1.pdf", "new_file": "file2.pdf"},
    )
    assert response.status_code == 200
    assert response.json() == "file2-a.pdf"
