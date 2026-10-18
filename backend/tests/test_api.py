"""HTTP-level tests for auth and the resync endpoint (service layer mocked)."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.config import settings
from app.routes import product_routes
from app.services.product_service import ProductService


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(product_routes.router)
    return TestClient(app)


def test_resync_endpoint_exists(client, monkeypatch):
    monkeypatch.setattr(settings, "ADMIN_API_KEY", "")
    monkeypatch.setattr(ProductService, "resync_failed", staticmethod(lambda: {"resynced": 2, "still_failed": 0}))
    r = client.post("/resync")
    assert r.status_code == 200
    assert r.json() == {"resynced": 2, "still_failed": 0}


def test_writes_require_key_when_configured(client, monkeypatch):
    monkeypatch.setattr(settings, "ADMIN_API_KEY", "secret")
    monkeypatch.setattr(ProductService, "delete_product", staticmethod(lambda pid: True))

    assert client.delete("/products/abc").status_code == 401
    assert client.delete("/products/abc", headers={"X-API-Key": "wrong"}).status_code == 401
    assert client.delete("/products/abc", headers={"X-API-Key": "secret"}).status_code == 200


def test_search_requires_query(client):
    assert client.get("/search").status_code == 422
