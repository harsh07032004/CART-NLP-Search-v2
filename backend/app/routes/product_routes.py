import secrets

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from typing import List, Optional
from app.config import settings
from app.models import ProductCreate, ProductUpdate, ProductResponse
from app.services.product_service import ProductService
from app.routes.insight_routes import log_search

router = APIRouter()


def require_admin(x_api_key: Optional[str] = Header(default=None)) -> None:
    """Protect write endpoints when ADMIN_API_KEY is configured.
    With no key configured (local dev / demo) writes stay open."""
    if settings.ADMIN_API_KEY and not (
        x_api_key and secrets.compare_digest(x_api_key, settings.ADMIN_API_KEY)
    ):
        raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key")

# NLP readiness flag — injected by main.py at startup
_nlp_ready = False

def set_nlp_ready(value: bool):
    global _nlp_ready
    _nlp_ready = value


@router.post("/products", response_model=ProductResponse, status_code=201, dependencies=[Depends(require_admin)])
async def create_product(product: ProductCreate):
    """Add a new product. Syncs to MongoDB + Elasticsearch."""
    try:
        return ProductService.create_product(product)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search", response_model=List[dict])
async def search_products(
    q: str = Query(..., min_length=1),
    size: int = Query(default=100, ge=1, le=200),
):
    """NLP-powered product search. Falls back to plain text if NLP engine not ready."""
    try:
        results = ProductService.search_products(q, size=size, nlp_ready=_nlp_ready)
        log_search(q, {}, len(results))
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/meta")
async def search_products_with_meta(
    q: str = Query(..., min_length=1),
    size: int = Query(default=100, ge=1, le=200),
):
    """NLP search that also returns what the AI parsed (entities, sort intent, did_you_mean).
    Used by SmartSearchBar to render entity chips with real data."""
    try:
        response = ProductService.search_products_with_meta(q, size=size, nlp_ready=_nlp_ready)
        log_search(q, response["parsed"], response["total"])
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/parse")
async def parse_search_query(q: str = Query(..., min_length=1)):
    """Return what the NLP engine parsed from a query — without executing the search.
    Useful for the front-end SmartSearchBar to show 'AI understood' chips in real time."""
    try:
        from app.utils.query_parser import parse_query
        parsed = parse_query(q)
        return {"query": q, "parsed": parsed}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/autocomplete")
async def autocomplete(
    q: str = Query(..., min_length=1),
    limit: int = Query(default=6, ge=1, le=12),
):
    """Return autocomplete suggestions (entity matches + top product name prefixes).
    Designed for < 100 ms response — called on every keystroke."""
    try:
        return ProductService.autocomplete(q, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/products", response_model=List[dict])
async def get_products(limit: int = Query(default=200, ge=1, le=500)):
    """Get all products (cached 5 min)."""
    try:
        return ProductService.get_all_products(limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/products/{product_id}", response_model=dict)
async def get_product(product_id: str):
    """Get a single product by ID."""
    product = ProductService.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.put("/products/{product_id}", response_model=dict, dependencies=[Depends(require_admin)])
async def update_product(product_id: str, updates: ProductUpdate):
    """Update an existing product."""
    try:
        updated = ProductService.update_product(product_id, updates)
        if not updated:
            raise HTTPException(status_code=404, detail="Product not found")
        return updated
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/products/{product_id}", dependencies=[Depends(require_admin)])
async def delete_product(product_id: str):
    """Delete a product from MongoDB and Elasticsearch."""
    try:
        success = ProductService.delete_product(product_id)
        return {"deleted": success, "product_id": product_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refresh-nlp", dependencies=[Depends(require_admin)])
async def refresh_nlp():
    """Manually trigger reload of brands/categories from DB into NLP parser."""
    try:
        from app.db import es_client, settings
        from app.utils.query_parser import update_entities

        res = es_client.search(
            index=settings.ES_INDEX,
            body={
                "size": 0,
                "aggs": {
                    "unique_brands": {"terms": {"field": "brand", "size": 1000}},
                    "unique_categories": {"terms": {"field": "category", "size": 100}},
                },
            },
        )
        brands = [b["key"] for b in res["aggregations"]["unique_brands"]["buckets"]]
        categories = [c["key"] for c in res["aggregations"]["unique_categories"]["buckets"]]

        if brands or categories:
            update_entities(new_brands=brands, new_categories=categories)

        set_nlp_ready(True)
        return {
            "status": "success",
            "message": "NLP Knowledge Base Refreshed",
            "brands": len(brands),
            "categories": len(categories),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/resync", dependencies=[Depends(require_admin)])
async def resync_failed_writes():
    """Replay Elasticsearch writes that failed after all retries
    (logged in the MongoDB `sync_failures` collection)."""
    try:
        return ProductService.resync_failed()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sync-status")
async def sync_status():
    """How many MongoDB writes are still missing from Elasticsearch."""
    try:
        return ProductService.sync_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
