from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import papis.zenodo
from papis.sources.handler import FileReference, LookupInput
from papis.sources.handlers.zenodo import ZenodoHandler

if TYPE_CHECKING:
    from typing import Any

    from papis.testing import TemporaryConfiguration

_FILE_URL = "https://zenodo.org/api/records/7391177/files/a.pdf/content"


@pytest.mark.parametrize(
    ("input_str", "expected_record_id"),
    [
        ("7391177", "7391177"),
        ("abc", None),
        # an ISBN-13 shape is not a Zenodo record ID
        ("9780486670478", None),
        # only the 978/979 prefixes are excluded
        ("1234567890123", "1234567890123"),
        ("13 97", None),
        ("", None),
    ],
)
def test_match(input_str: str, expected_record_id: str | None) -> None:
    instance = ZenodoHandler.match_for_lookup(LookupInput(input=input_str))
    if expected_record_id is None:
        assert instance is None
    else:
        assert instance is not None
        assert instance.record_id == expected_record_id


def test_lookup(
    tmp_config: TemporaryConfiguration, monkeypatch: pytest.MonkeyPatch
) -> None:
    record: dict[str, Any] = {
        "metadata": {
            "title": "Zenodo paper",
            "creators": [{"name": "Somebody"}],
        },
        "files": [
            {
                "key": "a.pdf",
                "links": {"self": _FILE_URL},
            },
        ],
    }
    monkeypatch.setattr(papis.zenodo, "get_data", lambda record_id: record)

    result = ZenodoHandler("7391177").lookup(LookupInput(input="7391177"))
    assert result.document is not None
    assert result.document["title"] == "Zenodo paper"
    assert result.files == [
        FileReference(url=_FILE_URL, filename="a.pdf", extension="pdf")
    ]
