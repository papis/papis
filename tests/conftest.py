import pytest

from tests import testlib


@pytest.fixture()
def tmp_config(request):
    marker = request.node.get_closest_marker("runner_setup")
    kwargs = marker.kwargs if marker else {}

    with testlib.TemporaryConfiguration(**kwargs) as config:
        yield config


@pytest.fixture()
def tmp_library(request):
    marker = request.node.get_closest_marker("runner_setup")
    kwargs = marker.kwargs if marker else {}

    with testlib.TemporaryLibrary(**kwargs) as lib:
        yield lib


@pytest.fixture()
def resource_cache():
    return testlib.ResourceCache(cachedir="resources")


@pytest.fixture()
def downloader_cache():
    return testlib.ResourceCache(cachedir="downloaders/resources")
