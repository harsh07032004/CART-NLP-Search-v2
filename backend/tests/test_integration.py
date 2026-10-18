"""
End-to-end tests against real Elasticsearch + MongoDB.

Skipped automatically unless ES is reachable at ES_HOST (CI starts both as
service containers; locally run `docker compose up -d elasticsearch mongo`).
"""

import time
import uuid

import pytest
import requests

from app.config import settings

try:
    requests.get(settings.ES_HOST, timeout=2).raise_for_status()
    ES_UP = True
except Exception:
    ES_UP = False

pytestmark = pytest.mark.skipif(not ES_UP, reason="Elasticsearch not reachable")

PRODUCTS = [
    {"name": "Air Zoom Running Shoes", "category": "shoes", "brand": "nike", "price": 2499, "color": "red", "gender": "men", "rating": 4.5, "discount": 20, "stock": 10},
    {"name": "Ultraboost Sneakers", "category": "shoes", "brand": "adidas", "price": 5999, "color": "black", "gender": "women", "rating": 4.7, "discount": 0, "stock": 5},
    {"name": "Classic Trainers", "category": "shoes", "brand": "puma", "price": 1799, "color": "white", "gender": "unisex", "rating": 4.1, "discount": 10, "stock": 0},
    {"name": "Galaxy 5G Phone", "category": "phone", "brand": "samsung", "price": 24999, "color": "blue", "gender": "unisex", "rating": 4.4, "discount": 5, "stock": 20},
]


@pytest.fixture(scope="module")
def client():
    from fastapi.testclient import TestClient
    from app.db import es_client, product_collection
    import main

    settings.ES_INDEX = f"test-products-{uuid.uuid4().hex[:8]}"
    settings.ADMIN_API_KEY = ""
    with TestClient(main.app) as c:
        # wait for background NLP loader to flip the readiness flag
        for _ in range(50):
            if c.get("/health").json()["nlp_ready"]:
                break
            time.sleep(0.1)
        for p in PRODUCTS:
            assert c.post("/products", json=p).status_code == 201
        yield c
        product_collection.delete_many({"name": {"$in": [p["name"] for p in PRODUCTS]}})
        es_client.indices.delete(index=settings.ES_INDEX, ignore=[404])


def names(results):
    return [r["name"] for r in results]


def test_structured_filters(client):
    r = client.get("/search", params={"q": "nike shoes under 3000"}).json()
    assert names(r) == ["Air Zoom Running Shoes"]


def test_sort_intent(client):
    r = client.get("/search", params={"q": "cheapest shoes"}).json()
    prices = [p["price"] for p in r]
    assert prices == sorted(prices) and len(prices) == 3


def test_in_stock_filter(client):
    r = client.get("/search", params={"q": "shoes in stock"}).json()
    assert "Classic Trainers" not in names(r)


def test_fallback_relaxes_brand_but_keeps_category(client):
    # no reebok shoes exist -> brand relaxed, still only shoes
    r = client.get("/search", params={"q": "reebok shoes"}).json()
    assert r and all(p["category"] == "shoes" for p in r)


def test_meta_and_did_you_mean(client):
    r = client.get("/search/meta", params={"q": "samusng phone"}).json()
    assert r["parsed"]["brand"] == "samsung"
    assert r["did_you_mean"] == "samsung phone"
    assert names(r["results"]) == ["Galaxy 5G Phone"]


def test_similar_products_same_category(client):
    shoe = client.get("/search", params={"q": "nike shoes"}).json()[0]
    r = client.get(f"/recommendations/similar/{shoe['id']}").json()
    sims = r["similar_products"]
    assert sims and all(p["category"] == "shoes" and p["id"] != shoe["id"] for p in sims)


def test_update_is_visible_immediately(client):
    shoe = client.get("/search", params={"q": "adidas shoes"}).json()[0]
    client.put(f"/products/{shoe['id']}", json={"price": 999})
    again = client.get("/search", params={"q": "adidas shoes"}).json()[0]
    assert again["price"] == 999  # cache was invalidated


def test_analytics_records_searches(client):
    client.get("/search/meta", params={"q": "zzzz nothing matches"})
    stats = client.get("/analytics/stats", params={"days": 1}).json()
    assert stats["total_searches"] >= 1


def test_resync_and_status(client):
    assert client.post("/resync").status_code == 200
    assert "pending_failures" in client.get("/sync-status").json()
