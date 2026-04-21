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
    import json

    response = client.post(
        "/api/v1/libraries/test/documents",
        data={"data": json.dumps({"title": title}), "folder": path},
    )
    assert response.status_code == 201
    return response.json()["document"]["papis_id"], path


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
    assert data == {"files": []}


def test_list_files(tmp_config: TemporaryConfiguration) -> None:
    """GET .../files returns list of files in document."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, _ = create_test_document(client)

    response1 = client.post(
        f"/api/v1/libraries/test/documents/{papis_id}/files",
        files={"file_upload": ("file1.pdf", BytesIO(b"Content 1"), "application/pdf")},
    )
    assert response1.status_code == 201
    response2 = client.post(
        f"/api/v1/libraries/test/documents/{papis_id}/files",
        files={"file_upload": ("file2.pdf", BytesIO(b"Content 2"), "application/pdf")},
    )
    assert response2.status_code == 201

    list_response = client.get(f"/api/v1/libraries/test/documents/{papis_id}/files")
    files = list_response.json()["files"]
    assert "file1.pdf" in [f["name"] for f in files]
    assert "file2.pdf" in [f["name"] for f in files]


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
        files={"file_upload": ("test.pdf", BytesIO(file_content), "application/pdf")},
    )

    assert response.status_code == 201

    list_response = client.get(f"/api/v1/libraries/test/documents/{papis_id}/files")
    assert list_response.status_code == 200
    assert "test.pdf" in [f["name"] for f in list_response.json()["files"]]

    # Verify on disk
    file_path = os.path.join(tmp_config.libdir, path, "test.pdf")
    assert os.path.exists(file_path)
    with open(file_path, "rb") as f:
        assert f.read() == file_content


def test_add_file_path_normalization(tmp_config: TemporaryConfiguration) -> None:
    """POST .../files normalizes special characters to safe filenames."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, _ = create_test_document(client)

    response = client.post(
        f"/api/v1/libraries/test/documents/{papis_id}/files",
        files={
            "file_upload": (
                "test!!file<>with/special*chars.pdf",
                BytesIO(b"Test content"),
                "application/pdf",
            )
        },
    )
    assert response.status_code == 201

    # Verify on disk
    list_response = client.get(f"/api/v1/libraries/test/documents/{papis_id}/files")
    files = list_response.json()["files"]
    # / in filename treated as path separator, only basename preserved
    assert files == [{"name": "special-chars.pdf"}]


def test_add_file_unique_name_suffix(tmp_config: TemporaryConfiguration) -> None:
    """POST .../files adds suffix to avoid filename clashes."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, _ = create_test_document(client)

    response1 = client.post(
        f"/api/v1/libraries/test/documents/{papis_id}/files",
        files={
            "file_upload": ("document.pdf", BytesIO(b"Content 1"), "application/pdf")
        },
    )
    assert response1.status_code == 201
    assert response1.json()["name"] == "document.pdf"

    response2 = client.post(
        f"/api/v1/libraries/test/documents/{papis_id}/files",
        files={
            "file_upload": ("document.pdf", BytesIO(b"Content 2"), "application/pdf")
        },
    )
    assert response2.status_code == 201
    assert response2.json()["name"] == "document-a.pdf"


def test_add_file_unique_name_suffix_non_file(
    tmp_config: TemporaryConfiguration,
) -> None:
    """POST .../files adds suffix when filename clashes with existing note."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, _ = create_test_document(client)

    client.post(
        f"/api/v1/libraries/test/documents/{papis_id}/notes",
        files={"file_upload": ("notes.tex", BytesIO(b"Note content"), "text/plain")},
    )

    response = client.post(
        f"/api/v1/libraries/test/documents/{papis_id}/files",
        files={"file_upload": ("notes.tex", BytesIO(b"File content"), "text/plain")},
    )

    assert response.status_code == 201
    assert response.json()["name"] == "notes-a.tex"


def test_add_file_file_name_wins_over_config(
    tmp_config: TemporaryConfiguration,
) -> None:
    """POST .../files file_name form field takes priority over add-file-name config."""
    import papis.config
    from papis.server.app import app

    papis.config.set("add-file-name", "config-name")

    client = TestClient(app)
    papis_id, _ = create_test_document(client)

    response = client.post(
        f"/api/v1/libraries/test/documents/{papis_id}/files",
        data={"filename": "explicit-name"},
        files={"file_upload": ("test.pdf", BytesIO(b"content"), "application/pdf")},
    )

    assert response.status_code == 201
    assert response.json()["name"] == "explicit-name.pdf"


def test_add_file_file_name_with_extension(
    tmp_config: TemporaryConfiguration,
) -> None:
    """POST .../files file_name with extension doesn't get duplicated."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, _ = create_test_document(client)

    response = client.post(
        f"/api/v1/libraries/test/documents/{papis_id}/files",
        data={"filename": "explicit-name.pdf"},
        files={"file_upload": ("test.pdf", BytesIO(b"content"), "application/pdf")},
    )

    assert response.status_code == 201
    assert response.json()["name"] == "explicit-name.pdf"


def test_add_file_respects_config(tmp_config: TemporaryConfiguration) -> None:
    """POST .../files uses add-file-name config when no file_name given."""
    import papis.config
    from papis.server.app import app

    papis.config.set("add-file-name", "from-config")

    client = TestClient(app)
    papis_id, _ = create_test_document(client)

    response = client.post(
        f"/api/v1/libraries/test/documents/{papis_id}/files",
        files={
            "file_upload": ("ignored-name.pdf", BytesIO(b"content"), "application/pdf")
        },
    )

    assert response.status_code == 201
    assert response.json()["name"] == "from-config.pdf"


def test_document_not_found(tmp_config: TemporaryConfiguration) -> None:
    """POST .../files returns 404 for non-existent document."""
    from papis.server.app import app

    client = TestClient(app)

    response = client.get("/api/v1/libraries/test/documents/nonexistent-id/files")
    assert response.status_code == 404

    response = client.post(
        "/api/v1/libraries/test/documents/nonexistent-id/files",
        files={"file_upload": ("test.pdf", BytesIO(b"Content"), "application/pdf")},
    )
    assert response.status_code == 404


def test_add_file_via_symlink(tmp_config: TemporaryConfiguration) -> None:
    """POST .../files with link_file creates a symlink (local mode)."""
    import tempfile

    from papis.server.app import app

    client = TestClient(app)
    papis_id, doc_path = create_test_document(client)

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    ) as f:
        f.write("hello from symlink")
        src_path = f.name

    try:
        response = client.post(
            f"/api/v1/libraries/test/documents/{papis_id}/files",
            data={"link_file": src_path},
        )

        assert response.status_code == 201
        filename = response.json()["name"]

        list_response = client.get(f"/api/v1/libraries/test/documents/{papis_id}/files")
        assert filename in [f["name"] for f in list_response.json()["files"]]

        file_on_disk = os.path.join(tmp_config.libdir, doc_path, filename)
        assert os.path.islink(file_on_disk)
        assert os.path.samefile(os.readlink(file_on_disk), src_path)
    finally:
        os.unlink(src_path)


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
        files={
            "file_upload": ("download.pdf", BytesIO(file_content), "application/pdf")
        },
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
    from papis.server.routes.libraries import get_db

    client = TestClient(app)
    papis_id, doc_path = create_test_document(
        client, path="special-chars-test", title="Special Chars File Test"
    )

    special_filename = "test%file.pdf"
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
            "file_upload": (
                "original.pdf",
                BytesIO(b"Original content"),
                "application/pdf",
            )
        },
    )

    new_content = b"Replaced content"
    response = client.put(
        f"/api/v1/libraries/test/documents/{papis_id}/files/original.pdf",
        files={
            "file_upload": ("original.pdf", BytesIO(new_content), "application/pdf")
        },
    )

    assert response.status_code == 200
    assert response.json()["name"] == "original.pdf"

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
        files={
            "file_upload": ("nonexistent.pdf", BytesIO(b"Content"), "application/pdf")
        },
    )

    assert response.status_code == 404


def test_replace_file_with_special_chars(tmp_config: TemporaryConfiguration) -> None:
    """PUT .../files/{file} can replace a file with special characters in name."""
    from papis.document import Document
    from papis.server.app import app
    from papis.server.routes.libraries import get_db

    client = TestClient(app)
    papis_id, doc_path = create_test_document(
        client, path="special-chars-test", title="Special Chars File Test"
    )

    special_filename = "test%file.pdf"
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
            "file_upload": (
                special_filename,
                BytesIO(b"new content"),
                "application/pdf",
            )
        },
    )
    assert response.status_code == 200
    assert response.json()["name"] == special_filename


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
        files={
            "file_upload": ("todelete.pdf", BytesIO(b"To delete"), "application/pdf")
        },
    )

    response = client.delete(
        f"/api/v1/libraries/test/documents/{papis_id}/files/todelete.pdf"
    )

    assert response.status_code == 204

    list_response = client.get(f"/api/v1/libraries/test/documents/{papis_id}/files")
    assert "todelete.pdf" not in [f["name"] for f in list_response.json()["files"]]

    # Verify on disk
    file_path = os.path.join(tmp_config.libdir, path, "todelete.pdf")
    assert not os.path.exists(file_path), "File should be deleted from disk"


def test_delete_file_missing_on_disk(tmp_config: TemporaryConfiguration) -> None:
    """DELETE .../files/{file} cleans up metadata even when file is gone."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, doc_path = create_test_document(
        client, path="delete-stale-file", title="Delete Stale File"
    )

    client.post(
        f"/api/v1/libraries/test/documents/{papis_id}/files",
        files={"file_upload": ("gone.pdf", BytesIO(b"content"), "application/pdf")},
    )
    os.unlink(os.path.join(tmp_config.libdir, doc_path, "gone.pdf"))

    response = client.delete(
        f"/api/v1/libraries/test/documents/{papis_id}/files/gone.pdf"
    )
    assert response.status_code == 204

    list_response = client.get(f"/api/v1/libraries/test/documents/{papis_id}/files")
    assert "gone.pdf" not in [f["name"] for f in list_response.json()["files"]]


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
    from papis.server.routes.libraries import get_db

    client = TestClient(app)
    papis_id, doc_path = create_test_document(
        client, path="special-chars-test", title="Special Chars File Test"
    )

    special_filename = "test%file.pdf"
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
    assert client.get(f"/api/v1/libraries/test/documents/{papis_id}/files").json() == {
        "files": []
    }


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
        files={"file_upload": ("oldname.pdf", BytesIO(b"Content"), "application/pdf")},
    )

    response = client.patch(
        f"/api/v1/libraries/test/documents/{papis_id}/files/oldname.pdf",
        json={"filename": "newname.pdf"},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "newname.pdf"

    list_response = client.get(f"/api/v1/libraries/test/documents/{papis_id}/files")
    files = list_response.json()["files"]
    assert "newname.pdf" in [f["name"] for f in files]
    assert "oldname.pdf" not in [f["name"] for f in files]

    # Verify on disk
    old_file = os.path.join(tmp_config.libdir, path, "oldname.pdf")
    new_file = os.path.join(tmp_config.libdir, path, "newname.pdf")
    assert os.path.exists(new_file)
    assert not os.path.exists(old_file)


def test_rename_file_preserves_extension(tmp_config: TemporaryConfiguration) -> None:
    """PATCH .../files preserves the original file extension when body has none."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, _ = create_test_document(client)

    client.post(
        f"/api/v1/libraries/test/documents/{papis_id}/files",
        files={"file_upload": ("paper.pdf", BytesIO(b"Content"), "application/pdf")},
    )

    response = client.patch(
        f"/api/v1/libraries/test/documents/{papis_id}/files/paper.pdf",
        json={"filename": "newname"},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "newname.pdf"


def test_rename_file_not_found(tmp_config: TemporaryConfiguration) -> None:
    """PATCH .../files returns 404 when old file not in document."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, _ = create_test_document(client)

    response = client.patch(
        f"/api/v1/libraries/test/documents/{papis_id}/files/nonexistent.pdf",
        json={"filename": "new.pdf"},
    )

    assert response.status_code == 404


def test_rename_file_path_normalization(tmp_config: TemporaryConfiguration) -> None:
    """PATCH .../files normalizes special characters in new filename."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, path = create_test_document(client)

    client.post(
        f"/api/v1/libraries/test/documents/{papis_id}/files",
        files={"file_upload": ("oldname.pdf", BytesIO(b"Content"), "application/pdf")},
    )

    response = client.patch(
        f"/api/v1/libraries/test/documents/{papis_id}/files/oldname.pdf",
        json={"filename": "new!!name<>with/special*chars.pdf"},
    )
    assert response.status_code == 200

    list_response = client.get(f"/api/v1/libraries/test/documents/{papis_id}/files")
    files = list_response.json()["files"]
    assert files == [{"name": "new-name-with-special-chars.pdf"}]

    # Verify on disk
    old_file = os.path.join(tmp_config.libdir, path, "oldname.pdf")
    new_file = os.path.join(tmp_config.libdir, path, "new-name-with-special-chars.pdf")
    assert os.path.exists(new_file), "New file should exist on disk"
    assert not os.path.exists(old_file), "Old file should be renamed (deleted)"


def test_rename_file_self_rename(tmp_config: TemporaryConfiguration) -> None:
    """PATCH .../files returns the same name when renaming to itself."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, path = create_test_document(client)

    content = b"Original content"
    client.post(
        f"/api/v1/libraries/test/documents/{papis_id}/files",
        files={"file_upload": ("doc.pdf", BytesIO(content), "application/pdf")},
    )

    response = client.patch(
        f"/api/v1/libraries/test/documents/{papis_id}/files/doc.pdf",
        json={"filename": "doc.pdf"},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "doc.pdf"

    # Verify file still exists with original content
    file_path = os.path.join(tmp_config.libdir, path, "doc.pdf")
    assert os.path.exists(file_path)
    with open(file_path, "rb") as f:
        assert f.read() == content


def test_rename_file_unique_name_suffix(tmp_config: TemporaryConfiguration) -> None:
    """PATCH .../files adds suffix to avoid filename clashes."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, _ = create_test_document(client)

    client.post(
        f"/api/v1/libraries/test/documents/{papis_id}/files",
        files={"file_upload": ("file1.pdf", BytesIO(b"Content 1"), "application/pdf")},
    )
    client.post(
        f"/api/v1/libraries/test/documents/{papis_id}/files",
        files={"file_upload": ("file2.pdf", BytesIO(b"Content 2"), "application/pdf")},
    )

    response = client.patch(
        f"/api/v1/libraries/test/documents/{papis_id}/files/file1.pdf",
        json={"filename": "file2.pdf"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "file2-a.pdf"
