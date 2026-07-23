"""Tests for the /libraries/{library}/config endpoint."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi.testclient import TestClient

if TYPE_CHECKING:
    from papis.testing import TemporaryConfiguration


# =============================================================================
# GET /api/v1/libraries/{library}/config
# =============================================================================

LIBRARY = "test"
CONFIG_URL = f"/api/v1/libraries/{LIBRARY}/config"


def test_get_config_returns_200(tmp_config: TemporaryConfiguration) -> None:
    """GET /libraries/{library}/config returns 200 and a ConfigResponse."""
    from papis.server.app import app

    client = TestClient(app)
    response = client.get(CONFIG_URL)

    assert response.status_code == 200
    data = response.json()
    assert "sections" in data
    assert isinstance(data["sections"], dict)


def test_get_config_has_expected_sections(tmp_config: TemporaryConfiguration) -> None:
    """GET /libraries/{library}/config returns settings and tui sections."""
    from papis.server.app import app

    client = TestClient(app)
    response = client.get(CONFIG_URL)

    sections = response.json()["sections"]
    assert "settings" in sections
    assert "tui" in sections


def test_get_config_path_keys_omitted(tmp_config: TemporaryConfiguration) -> None:
    """Path-like keys are omitted from all sections when not in local mode."""
    import papis.config

    papis.config.set("server-local-mode", False)

    from papis.server.app import app

    client = TestClient(app)
    response = client.get(CONFIG_URL)

    sections = response.json()["sections"]
    path_keys = {"dir", "dirs", "cache-dir", "header-format-file", "local-config-file"}
    for _, section_data in sections.items():
        for key in path_keys:
            assert key not in section_data


def test_get_config_reflects_user_overrides(
    tmp_config: TemporaryConfiguration,
) -> None:
    """User-set config values override defaults in the API response."""
    from papis import config as papis_config

    papis_config.set("default-library", "my-custom-lib")

    from papis.server.app import app

    client = TestClient(app)
    response = client.get(CONFIG_URL)

    sections = response.json()["sections"]
    assert sections["settings"]["default-library"] == "my-custom-lib"


def test_get_config_no_raw_library_sections(
    tmp_config: TemporaryConfiguration,
) -> None:
    """Raw library sections (with dir paths) are never exposed."""
    from papis.server.app import app

    client = TestClient(app)
    response = client.get(CONFIG_URL)

    sections = response.json()["sections"]
    # Library sections (like "test") contain dir/paths — they must not leak
    assert LIBRARY not in sections


def test_get_config_library_not_found(
    tmp_config: TemporaryConfiguration,
) -> None:
    """GET /libraries/{library}/config returns 404 for unknown library."""
    from papis.server.app import app

    client = TestClient(app)
    response = client.get("/api/v1/libraries/nonexistent/config")

    assert response.status_code == 404


def test_get_config_sentinels_omitted(
    tmp_config: TemporaryConfiguration,
) -> None:
    """Sentinel object() values are omitted from the config response."""
    from papis.server.app import app

    client = TestClient(app)
    response = client.get(CONFIG_URL)

    sections = response.json()["sections"]
    # Sentinel keys (for deprecated fields) should not appear
    sentinel_keys = {
        "doctor-keys-exist-keys",
        "doctor-key-type-check-keys",
        "doctor-key-type-check-separator",
        "doctor-key-type-keys",
        "doctor-key-type-keys-extend",
        "doctor-key-type-separator",
        "formater",
    }
    settings = sections.get("settings", {})
    for key in sentinel_keys:
        assert key not in settings


def test_get_config_path_keys_present_in_local_mode(
    tmp_config: TemporaryConfiguration,
) -> None:
    """Path and tool keys are included in local mode."""

    from papis.server.app import app

    client = TestClient(app)
    response = client.get(CONFIG_URL)

    sections = response.json()["sections"]
    settings = sections.get("settings", {})
    assert "browser" in settings
    assert "editor" in settings


# =============================================================================
# X-Papis-Config-Override header
# =============================================================================


def test_config_override_header(tmp_config: TemporaryConfiguration) -> None:
    """The X-Papis-Config-Override header overrides config for a single request."""
    import json

    from papis.server.app import app

    client = TestClient(app)
    before = client.get(CONFIG_URL).json()["sections"]
    original = before["settings"]["default-library"]

    overrides = {"settings": {"default-library": "ephemeral-lib"}}
    response = client.get(
        CONFIG_URL,
        headers={"X-Papis-Config-Override": json.dumps(overrides)},
    )
    assert response.status_code == 200
    sections = response.json()["sections"]
    assert sections["settings"]["default-library"] == "ephemeral-lib"

    after = client.get(CONFIG_URL).json()["sections"]
    assert after["settings"]["default-library"] == original


def test_config_override_header_restores_after_error(
    tmp_config: TemporaryConfiguration,
) -> None:
    """Config overrides are restored even when the handler raises an error."""
    import json

    from papis.server.app import app

    client = TestClient(app)
    original = client.get(CONFIG_URL).json()["sections"]["settings"]["default-library"]

    overrides = {"settings": {"default-library": "doomed"}}
    # This endpoint doesn't exist, so the handler will 404, but the override should
    # be restored.
    client.get(
        f"/api/v1/libraries/{LIBRARY}/documents/nonexistent-id",
        headers={"X-Papis-Config-Override": json.dumps(overrides)},
    )

    after = client.get(CONFIG_URL).json()["sections"]
    assert after["settings"]["default-library"] == original
