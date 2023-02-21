import os
import json
from typing import Any, Callable, Dict, Optional

from tests import with_default_config       # noqa: F401


DOWNLOADER_RESOURCES_PATH = os.path.join(os.path.dirname(__file__), "resources")

PAPIS_UPDATE_RESOURCES = os.environ.get("PAPIS_UPDATE_RESOURCES", "none").lower()
if PAPIS_UPDATE_RESOURCES not in ("none", "remote", "local", "both"):
    raise ValueError("unsupported value of 'PAPIS_UPDATE_RESOURCES'")


def get_resource(name: str) -> str:
    path = os.path.join(DOWNLOADER_RESOURCES_PATH, name)
    assert os.path.exists(path)

    with open(path, errors="ignore") as f:
        return f.read()


def get_json_resource(name: str) -> Any:
    return json.loads(get_resource(name))


def get_remote_resource(
        filename: str, url: str,
        force: bool = False,
        params: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
        cookies: Optional[Dict[str, str]] = None,
        ) -> Callable[[], bytes]:
    filename = os.path.join(DOWNLOADER_RESOURCES_PATH, filename)
    if force or PAPIS_UPDATE_RESOURCES in ("remote", "both"):
        import requests
        import papis.config

        if headers is None:
            headers = {}

        headers["User-Agent"] = papis.config.getstring("user-agent")
        response = requests.get(url, params=params, headers=headers, cookies=cookies)

        with open(filename, "w", encoding="utf-8") as f:
            f.write(response.content.decode())

    def factory() -> bytes:
        with open(filename, encoding="utf-8") as f:
            return f.read().encode()

    return factory


def get_local_resource(
        filename: str, data: Any,
        force: bool = False,
        ) -> Any:
    filename = os.path.join(DOWNLOADER_RESOURCES_PATH, filename)
    _, ext = os.path.splitext(filename)

    import yaml
    import papis.yaml

    if force or PAPIS_UPDATE_RESOURCES in ("local", "both"):
        assert data is not None
        with open(filename, "w", encoding="utf-8") as f:
            if ext == ".json":
                json.dump(
                    data, f,
                    indent=2,
                    sort_keys=True,
                    ensure_ascii=False,
                    )
            elif ext == ".yml" or ext == ".yaml":
                yaml.dump(
                    data, f,
                    indent=2,
                    sort_keys=True,
                    )
            else:
                raise ValueError("unknown file extension: '{}'".format(ext))

    with open(filename, "r", encoding="utf-8") as f:
        if ext == ".json":
            return json.load(f)
        elif ext == ".yml" or ext == ".yaml":
            return papis.yaml.yaml_to_data(filename)
        else:
            raise ValueError("unknown file extension: '{}'".format(ext))
