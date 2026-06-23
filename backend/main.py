import asyncio
import threading
import time
import requests as _requests

import numpy as np
if not hasattr(np, "float_"):
    np.float_ = np.float64

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import product_routes
from app.db import init_es_index
from contextlib import asynccontextmanager

# @app.on_event("startup")
# async def startup_event():
# new way to do the same 
@asynccontextmanager
async def lifespan(app : FastAPI):
    # 1. Ensure ES index exists with correct mapping
    init_es_index()

    # 2. Load NLP data in background (non-blocking — server accepts requests immediately)
    asyncio.create_task(_load_nlp_data())

    # 3. Start keep-alive daemon thread
    ka_thread = threading.Thread(target=_keep_alive_worker, daemon=True)
    ka_thread.start()
    print("Startup: Keep-alive thread started")

    yield  # Hand control back to FastAPI — server is now running

# ---------------------------------------------------------------------------
# App definition
# ---------------------------------------------------------------------------

app = FastAPI(
    title="CART — Smart E-Commerce Search",
    description="NLP-powered e-commerce search engine with Elasticsearch",
    version="3.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# NLP readiness flag
# Prevents half-initialised NLP state from being used during cold-start
# ---------------------------------------------------------------------------
_nlp_ready = False


async def _load_nlp_data():
    """Load brand/category entities from ES into the NLP parser. Sets the
    readiness flag so route handlers know it's safe to use parse_query()."""
    global _nlp_ready
    print("Startup: Loading NLP Knowledge Base...")
    try:
        from app.db import es_client, settings
        from app.utils.query_parser import update_entities, load_synonyms_from_db

        # Load synonyms persisted in MongoDB
        load_synonyms_from_db()

        # Pull brands + categories from Elasticsearch aggregations
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
            print(f"Startup: NLP loaded - {len(brands)} brands, {len(categories)} categories")

    except Exception as e:
        print(f"Warning: NLP startup load failed: {e}")
    finally:
        _nlp_ready = True
        # Inject the flag into the product routes module
        product_routes.set_nlp_ready(True)
        print("Startup: NLP is ready")


# ---------------------------------------------------------------------------
# Keep-Alive: self-ping thread to prevent Render free-tier spin-down
# ---------------------------------------------------------------------------

def _keep_alive_worker(interval_seconds: int = 600):
    """Daemon thread that pings /health every `interval_seconds` (default 10 min).
    Keeps the Render process warm so the next real request doesn't cold-boot.
    A slightly randomised delay prevents clock-aligned thundering herd."""
    # Wait for the server to fully start before the first ping
    time.sleep(30)
    while True:
        try:
            resp = _requests.get("http://localhost:8000/health", timeout=10)
            print(f"[KeepAlive] Heartbeat -> status {resp.status_code}")
        except Exception as e:
            print(f"[KeepAlive] Heartbeat failed (will retry next cycle): {e}")
        time.sleep(interval_seconds)


# ---------------------------------------------------------------------------
# Startup / Shutdown events
# ---------------------------------------------------------------------------



# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

app.include_router(product_routes.router)


@app.get("/")
def read_root():
    return {
        "message": "CART API is running!",
        "nlp_ready": _nlp_ready,
        "features": ["NLP Search", "Elasticsearch", "Keep-Alive"],
    }


@app.get("/health")
def health_check():
    """Health probe — used by keep-alive pinger and Render health checks."""
    return {"status": "healthy", "nlp_ready": _nlp_ready}


@app.get("/nlp-status")
def nlp_status():
    """Detailed NLP engine status — useful for debugging cold-start issues."""
    try:
        from app.utils.query_parser import BRANDS, RAW_CATEGORIES, SYNONYM_MAP
        return {
            "nlp_ready": _nlp_ready,
            "brand_count": len(BRANDS),
            "category_count": len(RAW_CATEGORIES),
            "synonym_groups": {k: len(v) for k, v in SYNONYM_MAP.items()},
        }
    except Exception as e:
        return {"nlp_ready": _nlp_ready, "error": str(e)}
