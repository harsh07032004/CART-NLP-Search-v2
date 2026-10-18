"""Search-service tests with a fake Elasticsearch client (no ES needed)."""

import pytest

from app.cache import cache
from app.services import product_service
from app.services.product_service import ProductService


class FakeES:
    """Returns hits only when the query's filter set satisfies `accept`."""

    def __init__(self, accept):
        self.accept = accept
        self.bodies = []

    def search(self, index, body):
        self.bodies.append(body)
        filters = body["query"]["bool"]["filter"]
        hits = [{"_id": "1", "_source": {"name": "x", "rating": 4.0}}] if self.accept(filters) else []
        return {"hits": {"hits": hits}}


def _keys(filters):
    out = set()
    for f in filters:
        kind = next(iter(f))
        out.add(next(iter(f[kind])))
    return out


@pytest.fixture(autouse=True)
def _clear_cache():
    cache.clear()
    yield
    cache.clear()


def test_fallback_drops_brand_first_and_keeps_category(monkeypatch):
    fake = FakeES(lambda f: "brand" not in _keys(f))
    monkeypatch.setattr(product_service, "es_client", fake)

    results = ProductService.search_products("nike jackets under 2000")

    assert results, "fallback should find results once brand is relaxed"
    assert len(fake.bodies) == 2  # original query + one relaxation step
    relaxed = _keys(fake.bodies[-1]["query"]["bool"]["filter"])
    assert "category" in relaxed and "price" in relaxed and "brand" not in relaxed


def test_fallback_never_drops_category(monkeypatch):
    fake = FakeES(lambda f: "category" not in _keys(f))  # only "anything" matches
    monkeypatch.setattr(product_service, "es_client", fake)

    assert ProductService.search_products("nike jackets under 2000") == []
    for body in fake.bodies:
        assert "category" in _keys(body["query"]["bool"]["filter"])


def test_sort_intent_routes_to_price_sort(monkeypatch):
    fake = FakeES(lambda f: True)
    monkeypatch.setattr(product_service, "es_client", fake)

    ProductService.search_products("cheapest adidas shoes")
    assert fake.bodies[0]["sort"][0] == {"price": {"order": "asc"}}


def test_color_and_gender_boost_but_do_not_filter(monkeypatch):
    fake = FakeES(lambda f: True)
    monkeypatch.setattr(product_service, "es_client", fake)

    ProductService.search_products("red shirts for men")
    q = fake.bodies[0]["query"]["bool"]
    assert {"color", "gender"}.isdisjoint(_keys(q["filter"]))
    should_fields = {next(iter(s["term"])) for s in q["should"]}
    assert {"color", "gender"} <= should_fields


def test_meta_search_parses_once(monkeypatch):
    fake = FakeES(lambda f: True)
    monkeypatch.setattr(product_service, "es_client", fake)
    calls = []
    real = product_service.parse_query
    monkeypatch.setattr(product_service, "parse_query", lambda q: calls.append(q) or real(q))

    out = ProductService.search_products_with_meta("nike shoes")
    assert out["total"] == 1
    assert len(calls) == 1


def test_writes_invalidate_cached_searches():
    cache.set("search:abc", [1], ttl=120)
    cache.set("all_products", [1], ttl=120)
    product_service._invalidate_caches()
    assert cache.get("search:abc") is None
    assert cache.get("all_products") is None
