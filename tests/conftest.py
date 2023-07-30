import os
import pytest

from tests import testlib


@pytest.fixture()
def tmp_config(request):
    marker = request.node.get_closest_marker("config_setup")
    kwargs = marker.kwargs if marker else {}

    with testlib.TemporaryConfiguration(**kwargs) as config:
        yield config


@pytest.fixture()
def tmp_library(request):
    marker = request.node.get_closest_marker("library_setup")
    kwargs = marker.kwargs if marker else {}

    with testlib.TemporaryLibrary(**kwargs) as lib:
        yield lib


@pytest.fixture()
def resource_cache(request):
    marker = request.node.get_closest_marker("resource_setup")

    cachedir = "resources"
    if marker:
        cachedir = marker.kwargs.get("cachedir", "resources")
        cachedir = os.path.join(*cachedir.split("/"))

    return testlib.ResourceCache(cachedir)
