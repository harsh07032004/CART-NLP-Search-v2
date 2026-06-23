"""
Product Service — handles create, search, get, update, delete with:
- Dual-write safety (MongoDB primary + Elasticsearch secondary with retry)
- sync_failures collection for divergence recovery
- Result caching (2-minute TTL per query string)
- Proper sorting and scoring
- Sort-intent awareness (cheapest, best rated, newest, etc.)
- Autocomplete suggestions from entity knowledge base
"""

import time
import json
from typing import List, Optional
from datetime import datetime

from bson import ObjectId
from app import models
from app.db import product_collection, es_client, db, settings
from app.utils.query_parser import parse_query, get_autocomplete_suggestions
from app.cache import cache, cache_key, cached

# Collection that logs ES-index failures for later resync
sync_failures = db["sync_failures"]

# ---------------------------------------------------------------------------
# Sort-intent → ES sort clause mapping
# ---------------------------------------------------------------------------
_SORT_INTENT_MAP = {
    "price_asc":     [{"price": {"order": "asc"}},  {"rating": {"order": "desc", "missing": 0}}],
    "price_desc":    [{"price": {"order": "desc"}}, {"rating": {"order": "desc", "missing": 0}}],
    "rating_desc":   [{"rating": {"order": "desc", "missing": 0}}, {"price": {"order": "asc"}}],
    "discount_desc": [{"discount": {"order": "desc", "missing": 0}}, {"rating": {"order": "desc", "missing": 0}}],
    "newest":        [{"created_at": {"order": "desc", "missing": "_last"}}, {"rating": {"order": "desc", "missing": 0}}],
}

# Default sort — relevance score first, then rating, then discount, then price
_DEFAULT_SORT = [
    {"_score": "desc"},
    {"rating": {"order": "desc", "missing": 0}},
    {"discount": {"order": "desc", "missing": 0}},
    {"price": {"order": "asc"}},
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _es_index_with_retry(doc_id: str, doc: dict, max_attempts: int = 3) -> bool:
    """Index a document into Elasticsearch with exponential-backoff retry.
    Returns True on success, False after all attempts fail."""
    for attempt in range(1, max_attempts + 1):
        try:
            es_client.index(index=settings.ES_INDEX, id=doc_id, body=doc)
            es_client.indices.refresh(index=settings.ES_INDEX)
            return True
        except Exception as e:
            print(f"ES index attempt {attempt}/{max_attempts} failed for {doc_id}: {e}")
            if attempt < max_attempts:
                time.sleep(0.5 * attempt)  # 0.5s, 1s back-off

    # All attempts failed — log to sync_failures
    try:
        sync_failures.update_one(
            {"mongo_id": doc_id},
            {"$set": {"mongo_id": doc_id, "doc": doc, "failed_at": datetime.utcnow()}},
            upsert=True,
        )
    except Exception as db_err:
        print(f"Failed to log sync failure: {db_err}")

    return False


def _map_hit(hit: dict) -> dict:
    """Normalize an ES hit into a consistent frontend-ready dict."""
    data = hit["_source"].copy()
    data["id"] = hit["_id"]
    # Computed average rating from userRatings array
    user_ratings = data.get("userRatings", [])
    if user_ratings:
        avg = sum(r.get("rating", 0) for r in user_ratings) / len(user_ratings)
        data.setdefault("rating", round(avg, 1))
    else:
        data.setdefault("rating", data.get("rating", 0.0))
    return data


# ---------------------------------------------------------------------------
# Service class
# ---------------------------------------------------------------------------

class ProductService:

    # ------------------------------------------------------------------
    # CREATE
    # ------------------------------------------------------------------
    @staticmethod
    def create_product(product: models.ProductCreate) -> models.ProductResponse:
        from app.utils.query_parser import update_entities, add_synonyms
        from app.utils.auto_synonyms import fetch_auto_synonyms

        product_dict = product.model_dump()

        # Normalise keyword fields to lowercase
        for field in ("category", "brand", "gender", "color"):
            if product_dict.get(field):
                product_dict[field] = product_dict[field].lower().strip()

        # Register new entity in NLP knowledge base
        update_entities(
            new_brands=[product_dict["brand"]],
            new_categories=[product_dict["category"]],
        )

        # Synonyms — use provided or auto-discover
        if product.synonyms:
            add_synonyms("brands", product_dict["brand"], product.synonyms)
            add_synonyms("categories", product_dict["category"], product.synonyms)
        else:
            auto_syns = fetch_auto_synonyms(product_dict["category"])
            if auto_syns:
                add_synonyms("categories", product_dict["category"], auto_syns)
                product_dict["synonyms"] = auto_syns

        product_dict["created_at"] = datetime.utcnow()

        # 1. MongoDB (primary)
        result = product_collection.insert_one(product_dict)
        str_id = str(result.inserted_id)

        # 2. Elasticsearch (secondary) — with retry
        es_doc = {k: v for k, v in product_dict.items() if k != "_id"}
        es_doc["mongo_id"] = str_id
        _es_index_with_retry(str_id, es_doc)

        # Invalidate product-list cache
        cache.delete("all_products")

        return models.ProductResponse(id=str_id, **product_dict)

    # ------------------------------------------------------------------
    # PROGRESSIVE FALLBACK — relax filters stepwise, NEVER drop category
    # ------------------------------------------------------------------
    @staticmethod
    def _progressive_fallback(
        must_clauses: list,
        filter_clauses: list,
        should_clauses: list,
        sort_clause: list,
        parsed: dict,
        size: int,
    ) -> list:
        """
        Relax filters stepwise when 0 results are returned.
        KEY RULE: category filter is NEVER dropped (prevents cross-category false positives).
        If a user asks for "jackets", we ONLY show jackets at every level.

        Relaxation order:
          Level 1: category + brand + price + discount (drop nothing — should_clauses still boost)
          Level 2: category + price + discount         (drop brand)
          Level 3: category + discount                 (drop price)
          Level 4: category only                       (drop discount — show all category items)
          Level 5: category + match_all (keyword typo) (drop keyword must, keep category)
          Level 6: match_all everywhere                (absolute last resort — only when NO category)
        """

        def _run_query(filters, override_must=None, include_should=True):
            active_must = override_must if override_must is not None else must_clauses
            active_should = should_clauses if include_should else []
            has_kw = bool(active_must) and any("multi_match" in m for m in active_must)
            body = {
                "size": min(size, 200),
                "min_score": 0.1 if has_kw else 0,
                "query": {
                    "bool": {
                        "must": active_must if active_must else [{"match_all": {}}],
                        "filter": filters,
                        "should": active_should,
                        "minimum_should_match": 0,
                    }
                },
                "sort": sort_clause,
            }
            try:
                res = es_client.search(index=settings.ES_INDEX, body=body)
                hits = [_map_hit(h) for h in res["hits"]["hits"]]
                if hits:
                    print(f"Fallback L{_run_query._level}: {len(hits)} results, {len(filters)} filters")
                _run_query._level += 1
                return hits
            except Exception as e:
                print(f"Fallback query error: {e}")
                return []

        _run_query._level = 1

        # Split filter_clauses by type
        category_f = [f for f in filter_clauses if "term" in f and "category" in f.get("term", {})]
        brand_f    = [f for f in filter_clauses if "term" in f and "brand" in f.get("term", {})]
        price_f    = [f for f in filter_clauses if "range" in f and "price" in f.get("range", {})]
        discount_f = [f for f in filter_clauses if "range" in f and "discount" in f.get("range", {})]
        stock_f    = [f for f in filter_clauses if "range" in f and "stock" in f.get("range", {})]

        match_all_must = [{"match_all": {}}]
        has_category = bool(category_f)

        # Level 1: drop nothing (just retry in case it was a transient issue)
        hits = _run_query(filter_clauses)
        if hits:
            return hits

        # Level 2: drop brand (keep category + price + discount + stock)
        hits = _run_query(category_f + price_f + discount_f + stock_f)
        if hits:
            return hits

        # Level 3: drop price too (keep category + discount + stock)
        hits = _run_query(category_f + discount_f + stock_f)
        if hits:
            return hits

        # Level 4: drop discount/stock filters (show full category range)
        # This is the crucial one: "50% off jackets" with no 50%+ jackets → show all jackets
        if category_f:
            hits = _run_query(category_f)
            if hits:
                return hits

        # Level 5: keyword may be a bad typo — use match_all + category
        if category_f:
            hits = _run_query(category_f, override_must=match_all_must, include_should=False)
            if hits:
                return hits

        # Level 6: absolute last resort — no category specified, show anything relevant
        if not has_category:
            hits = _run_query([], override_must=match_all_must, include_should=False)
            if hits:
                return hits

        return []

    # ------------------------------------------------------------------
    # SEARCH  (now sort-intent aware)
    # ------------------------------------------------------------------
    @staticmethod
    def search_products(query: str, size: int = 100, nlp_ready: bool = True) -> List[dict]:
        if not query or not query.strip():
            return []

        # Cache key per (query, size)
        ck = cache_key(query.lower().strip(), size)
        cached_result = cache.get(f"search:{ck}")
        if cached_result is not None:
            print(f"Cache HIT: search '{query}'")
            return cached_result

        must_clauses = []
        filter_clauses = []   # hard: category, brand, price, discount, stock
        should_clauses = []   # soft: color, gender (boost ranking, don't eliminate results)

        if nlp_ready:
            parsed = parse_query(query)
            print(f"NLP Parsed: {json.dumps(parsed, default=str)}")
        else:
            parsed = {
                "keywords": [query.strip()],
                "category": None, "brand": None,
                "color": None, "gender": None,
                "price_min": None, "price_max": None,
                "sort_by": None, "is_sale": False,
                "in_stock": False, "min_discount": None,
                "did_you_mean": None,
            }

        # Intent words that have been mapped to structured filters
        # Strip them so they don't pollute the text must clause
        _INTENT_NOISE = {
            "sale", "sell", "offer", "deal", "deals", "discount", "discounted",
            "clearance", "flash", "stock", "available", "availability",
        }
        effective_keywords = [kw for kw in parsed["keywords"] if kw not in _INTENT_NOISE]

        # ── Text / keyword must clause ────────────────────────────────────────
        if effective_keywords:
            must_clauses.append({
                "multi_match": {
                    "query": " ".join(effective_keywords),
                    "fields": ["name^5", "description^2", "brand^3", "category^3", "color^2"],
                    "fuzziness": "AUTO",
                    "minimum_should_match": "60%",
                }
            })

            # ── Hard filters (category, brand, price, discount, stock) ────────────
            # These MUST match — they represent core user intent.
        if parsed["category"]:
            filter_clauses.append({"term": {"category": parsed["category"]}})
        if parsed["brand"]:
            filter_clauses.append({"term": {"brand": parsed["brand"]}})

        price_filter = {}
        if parsed["price_min"] is not None:
            price_filter["gte"] = parsed["price_min"]
        if parsed["price_max"] is not None:
            price_filter["lte"] = parsed["price_max"]
        if price_filter:
            filter_clauses.append({"range": {"price": price_filter}})

        if parsed.get("min_discount"):
            filter_clauses.append({"range": {"discount": {"gte": parsed["min_discount"]}}})
        elif parsed.get("is_sale"):
            filter_clauses.append({"range": {"discount": {"gt": 0}}})

        if parsed.get("in_stock"):
            filter_clauses.append({"range": {"stock": {"gt": 0}}})

        # ── Soft boosts (color, gender) — raise relevance score, don't filter ─
        # "blue shirts" → blue shirts rank first, other colors still shown
        # "shirts for men" → men's & unisex rank above women's
        if parsed["color"]:
            should_clauses.append({"term": {"color": {"value": parsed["color"], "boost": 4.0}}})
        if parsed["gender"]:
            # Two separate term boosts (terms query doesn't support boost in ES 7.x)
            should_clauses.append({"term": {"gender": {"value": parsed["gender"], "boost": 2.5}}})
            should_clauses.append({"term": {"gender": {"value": "unisex", "boost": 1.5}}})

        # If nothing to search on, do match_all
        if not must_clauses and not filter_clauses and not should_clauses:
            must_clauses.append({"match_all": {}})

        sort_clause = _SORT_INTENT_MAP.get(parsed.get("sort_by"), _DEFAULT_SORT)

        search_body = {
            "size": min(size, 200),
            "min_score": 0.1 if must_clauses and effective_keywords else 0,
            "query": {
                "bool": {
                    "must": must_clauses if must_clauses else [{"match_all": {}}],
                    "filter": filter_clauses,
                    "should": should_clauses,
                    "minimum_should_match": 0,  # should = optional boost only
                }
            },
            "sort": sort_clause,
        }

        print(f"ES Query: {json.dumps(search_body, default=str)}")
        res = es_client.search(index=settings.ES_INDEX, body=search_body)
        results = [_map_hit(h) for h in res["hits"]["hits"]]

        # ── Progressive fallback — only when 0 results ────────────────────────
        # IMPORTANT: We never drop category. It is the most critical intent signal.
        if not results and filter_clauses:
            results = ProductService._progressive_fallback(
                must_clauses, filter_clauses, should_clauses, sort_clause, parsed, size
            )


        # Cache for 2 minutes
        cache.set(f"search:{ck}", results, ttl=120)
        return results

    # ------------------------------------------------------------------
    # SEARCH WITH METADATA (returns dict with results + did_you_mean)
    # ------------------------------------------------------------------
    @staticmethod
    def search_products_with_meta(query: str, size: int = 100, nlp_ready: bool = True) -> dict:
        """Like search_products but also returns parsed metadata for the frontend."""
        if not query or not query.strip():
            return {"results": [], "parsed": {}, "did_you_mean": None}

        parsed = parse_query(query) if nlp_ready else {
            "keywords": [query.strip()], "category": None, "brand": None,
            "color": None, "gender": None, "price_min": None, "price_max": None,
            "sort_by": None, "is_sale": False, "in_stock": False,
            "min_discount": None, "did_you_mean": None,
        }

        results = ProductService.search_products(query, size=size, nlp_ready=nlp_ready)
        return {
            "results": results,
            "parsed": {k: v for k, v in parsed.items() if k != "did_you_mean"},
            "did_you_mean": parsed.get("did_you_mean"),
            "total": len(results),
        }

    # ------------------------------------------------------------------
    # AUTOCOMPLETE
    # ------------------------------------------------------------------
    @staticmethod
    def autocomplete(prefix: str, limit: int = 6) -> dict:
        """Return autocomplete suggestions: entity matches + recent ES product names."""
        prefix = prefix.strip().lower()
        if not prefix:
            return {"suggestions": [], "products": []}

        # 1. Entity-level suggestions from NLP knowledge base
        entity_suggestions = get_autocomplete_suggestions(prefix, limit=limit)

        # 2. Product name prefix matches from ES
        try:
            es_res = es_client.search(
                index=settings.ES_INDEX,
                body={
                    "size": limit,
                    "query": {
                        "bool": {
                            "should": [
                                {"match_phrase_prefix": {"name": {"query": prefix, "max_expansions": 10}}},
                                {"prefix": {"brand": {"value": prefix}}},
                            ]
                        }
                    },
                    "_source": ["name", "brand", "category", "price", "image_url"],
                    "sort": [{"rating": {"order": "desc", "missing": 0}}],
                },
            )
            product_hints = [
                {
                    "id": h["_id"],
                    "name": h["_source"].get("name", ""),
                    "brand": h["_source"].get("brand", ""),
                    "category": h["_source"].get("category", ""),
                    "price": h["_source"].get("price", 0),
                    "image": h["_source"].get("image_url", ""),
                }
                for h in es_res["hits"]["hits"]
            ]
        except Exception as e:
            print(f"Autocomplete ES error: {e}")
            product_hints = []

        return {
            "suggestions": entity_suggestions,
            "products": product_hints,
        }

    # ------------------------------------------------------------------
    # GET ALL
    # ------------------------------------------------------------------
    @staticmethod
    def get_all_products(limit: int = 200) -> List[dict]:
        cached_result = cache.get("all_products")
        if cached_result is not None:
            print("Cache HIT: all_products")
            return cached_result

        res = es_client.search(
            index=settings.ES_INDEX,
            body={
                "query": {"match_all": {}},
                "size": min(limit, 500),
                "sort": [
                    {"rating": {"order": "desc", "missing": 0}},
                    {"discount": {"order": "desc", "missing": 0}},
                ],
            },
        )
        results = [_map_hit(h) for h in res["hits"]["hits"]]
        cache.set("all_products", results, ttl=300)  # 5 min
        return results

    # ------------------------------------------------------------------
    # GET ONE
    # ------------------------------------------------------------------
    @staticmethod
    def get_product(product_id: str) -> Optional[dict]:
        try:
            hit = es_client.get(index=settings.ES_INDEX, id=product_id)
            return _map_hit(hit)
        except Exception:
            # Fallback to MongoDB
            try:
                doc = product_collection.find_one({"_id": ObjectId(product_id)})
                if doc:
                    doc["id"] = str(doc.pop("_id"))
                    return doc
            except Exception:
                pass
            return None

    # ------------------------------------------------------------------
    # UPDATE
    # ------------------------------------------------------------------
    @staticmethod
    def update_product(product_id: str, updates: models.ProductUpdate) -> Optional[dict]:
        update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
        if not update_data:
            return ProductService.get_product(product_id)

        for field in ("category", "brand", "gender", "color"):
            if update_data.get(field):
                update_data[field] = update_data[field].lower().strip()

        try:
            product_collection.update_one(
                {"_id": ObjectId(product_id)},
                {"$set": {**update_data, "updated_at": datetime.utcnow()}},
            )
        except Exception as e:
            print(f"Mongo update failed: {e}")

        try:
            es_client.update(
                index=settings.ES_INDEX,
                id=product_id,
                body={"doc": update_data},
            )
            es_client.indices.refresh(index=settings.ES_INDEX)
        except Exception as e:
            print(f"ES update failed: {e}")

        cache.delete("all_products")
        return ProductService.get_product(product_id)

    # ------------------------------------------------------------------
    # DELETE
    # ------------------------------------------------------------------
    @staticmethod
    def delete_product(product_id: str) -> bool:
        success = False
        try:
            product_collection.delete_one({"_id": ObjectId(product_id)})
            success = True
        except Exception as e:
            print(f"Mongo delete failed: {e}")

        try:
            es_client.delete(index=settings.ES_INDEX, id=product_id)
            es_client.indices.refresh(index=settings.ES_INDEX)
        except Exception as e:
            print(f"ES delete failed: {e}")

        cache.delete("all_products")
        return success

    # ------------------------------------------------------------------
    # RESYNC
    # ------------------------------------------------------------------
    @staticmethod
    def resync_failed() -> dict:
        failures = list(sync_failures.find({}))
        resynced, still_failed = 0, 0
        for f in failures:
            mongo_id = f["mongo_id"]
            doc = f.get("doc", {})
            if _es_index_with_retry(mongo_id, doc, max_attempts=2):
                sync_failures.delete_one({"mongo_id": mongo_id})
                resynced += 1
            else:
                still_failed += 1

        cache.delete("all_products")
        return {"resynced": resynced, "still_failed": still_failed}
