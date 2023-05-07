import os

import pytest
from fastapi.testclient import TestClient
from wiremock.client import Mappings
from wiremock.constants import Config
from wiremock.testing.testcontainer import WireMockServer, wiremock_container

from product_mock.overview_service import app

from .utils import get_mappings, get_products

client = TestClient(app)


@pytest.fixture(scope="module")
@wiremock_container()
def wm_docker(_wm: WireMockServer):
    Config.base_url = _wm.url
    os.environ["PRODUCTS_SERVICE_HOST"] = "http://localhost"
    os.environ["PRODUCTS_SERVICE_PORT"] = str(_wm.port)
    [Mappings.create_mapping(mapping=mapping) for mapping in get_mappings()]

    yield _wm

    Mappings.delete_all_mappings()


def test_get_overview_default(wm_docker):
    resp = client.get("/overview")

    assert resp.status_code == 200
    assert resp.json() == {"products": get_products()}


def test_get_overview_with_filters(wm_docker):
    resp = client.get("/overview?category=Books")

    assert resp.status_code == 200
    assert resp.json() == {
        "products": list(filter(lambda p: p["category"] == "Books", get_products()))
    }
