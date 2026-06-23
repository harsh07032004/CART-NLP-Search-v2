from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from app.models import ProductCreate, ProductUpdate, ProductResponse
from app.services.product_service import ProductService

router = APIRouter()

# NLP readiness flag — injected by main.py at startup
_nlp_ready = False

def set_nlp_ready(value: bool):
    global _nlp_ready
    _nlp_ready = value


@router.post("/products", response_model=ProductResponse, status_code=201)
async def create_product(product: ProductCreate):
    """Add a new product. Syncs to MongoDB + Elasticsearch."""
    try:
        return ProductService.create_product(product)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search", response_model=List[dict])
async def search_products(
    q: str = Query(None, min_length=1),
    size: int = Query(default=100, ge=1, le=200),
):
    """NLP-powered product search. Falls back to plain text if NLP engine not ready."""
    try:
        return ProductService.search_products(q, size=size, nlp_ready=_nlp_ready)
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
        return ProductService.search_products_with_meta(q, size=size, nlp_ready=_nlp_ready)
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


@router.put("/products/{product_id}", response_model=dict)
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


@router.delete("/products/{product_id}")
async def delete_product(product_id: str):
    """Delete a product from MongoDB and Elasticsearch."""
    try:
        success = ProductService.delete_product(product_id)
        return {"deleted": success, "product_id": product_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refresh-nlp")
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
