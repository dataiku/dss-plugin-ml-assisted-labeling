import os

import dataikuapi
import pytest


@pytest.fixture(scope="session")
def dss_client():
    url = os.environ.get("DSS_URL")
    api_key = os.environ.get("DSS_API_KEY")
    if not url or not api_key:
        pytest.fail("Set DSS_URL and DSS_API_KEY to run integration tests against a DSS instance.")
    return dataikuapi.DSSClient(url, api_key)


@pytest.fixture
def app_project(dss_client):
    app = dss_client.get_app("PLUGIN_ml-assisted-labeling_object-detection")
    with app.create_temporary_instance() as instance:
        yield instance.get_as_project()
