"""
Recommendation + search-analytics endpoints.

These were already called by the frontend (`lib/api.js`) but had no backend,
so the "Similar products" strip on the product page was always empty.
"""

from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Query

from app.db import db, es_client, settings
from app.services.product_service import _map_hit

router = APIRouter()

search_logs = db["search_logs"]
click_logs = db["click_logs"]


def log_search(query: str, parsed: dict, total: int) -> None:
    """Record one search (best-effort: analytics must never break search)."""
    try:
        search_logs.insert_one({
            "query": query.lower().strip(),
            "category": parsed.get("category"),
            "brand": parsed.get("brand"),
            "results": total,
            "ts": datetime.utcnow(),
        })
    except Exception as e:
        print(f"Search log failed: {e}")


# ---------------------------------------------------------------------------
# Recommendations
# ---------------------------------------------------------------------------

@router.get("/recommendations/similar/{product_id}")
async def similar_products(product_id: str, limit: int = Query(default=6, ge=1, le=20)):
    """Content-based similar items: Elasticsearch more_like_this on name and
    description, restricted to the same category, boosted by same brand."""
    try:
        source = es_client.get(index=settings.ES_INDEX, id=product_id)["_source"]
    except Exception:
        raise HTTPException(status_code=404, detail="Product not found")

    should = [{
        "more_like_this": {
            "fields": ["name", "description"],
            "like": [{"_index": settings.ES_INDEX, "_id": product_id}],
            "min_term_freq": 1,
            "min_doc_freq": 1,
        }
    }]
    if source.get("brand"):
        should.append({"term": {"brand": {"value": source["brand"], "boost": 1.5}}})

    body = {
        "size": limit,
        "query": {
            "bool": {
                "filter": [{"term": {"category": source.get("category")}}],
                "must_not": [{"ids": {"values": [product_id]}}],
                "should": should,
                "minimum_should_match": 0,
            }
        },
        "sort": ["_score", {"rating": {"order": "desc", "missing": 0}}],
    }
    res = es_client.search(index=settings.ES_INDEX, body=body)
    return {"product_id": product_id, "similar_products": [_map_hit(h) for h in res["hits"]["hits"]]}


@router.get("/recommendations/trending")
async def trending_products(limit: int = Query(default=10, ge=1, le=50)):
    """Highest-rated in-stock products, ties broken by discount."""
    body = {
        "size": limit,
        "query": {"bool": {"filter": [{"range": {"stock": {"gt": 0}}}]}},
        "sort": [
            {"rating": {"order": "desc", "missing": 0}},
            {"discount": {"order": "desc", "missing": 0}},
        ],
    }
    res = es_client.search(index=settings.ES_INDEX, body=body)
    return {"trending_products": [_map_hit(h) for h in res["hits"]["hits"]]}


# ---------------------------------------------------------------------------
# Search analytics
# ---------------------------------------------------------------------------

@router.get("/analytics/stats")
async def analytics_stats(days: int = Query(default=7, ge=1, le=90)):
    """Search volume, zero-result rate and click-through rate for the window."""
    since = datetime.utcnow() - timedelta(days=days)
    total = search_logs.count_documents({"ts": {"$gte": since}})
    zero = search_logs.count_documents({"ts": {"$gte": since}, "results": 0})
    clicks = click_logs.count_documents({"ts": {"$gte": since}})
    return {
        "days": days,
        "total_searches": total,
        "zero_result_searches": zero,
        "zero_result_rate": round(zero / total, 4) if total else 0.0,
        "clicks": clicks,
        "click_through_rate": round(clicks / total, 4) if total else 0.0,
    }


@router.get("/analytics/top-searches")
async def top_searches(
    days: int = Query(default=7, ge=1, le=90),
    limit: int = Query(default=20, ge=1, le=100),
):
    """Most frequent queries, with how often each returned nothing."""
    since = datetime.utcnow() - timedelta(days=days)
    pipeline = [
        {"$match": {"ts": {"$gte": since}}},
        {"$group": {
            "_id": "$query",
            "count": {"$sum": 1},
            "zero_results": {"$sum": {"$cond": [{"$eq": ["$results", 0]}, 1, 0]}},
        }},
        {"$sort": {"count": -1}},
        {"$limit": limit},
    ]
    rows = list(search_logs.aggregate(pipeline))
    return {"top_searches": [
        {"query": r["_id"], "count": r["count"], "zero_results": r["zero_results"]} for r in rows
    ]}


@router.post("/analytics/click")
async def log_click(query: str, product_id: str, position: int = 0):
    """Record a result click (used for click-through rate)."""
    click_logs.insert_one({
        "query": query.lower().strip(),
        "product_id": product_id,
        "position": position,
        "ts": datetime.utcnow(),
    })
    return {"logged": True}
