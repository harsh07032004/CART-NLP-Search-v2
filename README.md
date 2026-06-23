# CART — NLP-Powered E-Commerce Search Engine

> **Full-stack placement project** demonstrating production-grade NLP, Elasticsearch search, and modern React development with a clean, deployable architecture.

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/Frontend-React_18-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![Elasticsearch](https://img.shields.io/badge/Search-Elasticsearch_7-005571?logo=elasticsearch&logoColor=white)](https://www.elastic.co/)
[![MongoDB](https://img.shields.io/badge/Database-MongoDB_Atlas-47A248?logo=mongodb&logoColor=white)](https://www.mongodb.com/)
[![Render](https://img.shields.io/badge/Deployed-Render-46E3B7?logo=render&logoColor=black)](https://render.com/)

---

## ✨ What This Project Does

**CART** is a smart e-commerce search engine where users type natural language queries like:

- *"cheapest red Nike shoes for men under ₹3000"*
- *"50% off jackets"*
- *"best rated Samsung phones"*
- *"samusng phone"* ← typo handled automatically

The backend **parses these queries with NLP**, extracts structured intent (brand, category, color, gender, price, sort order), and runs a targeted **Elasticsearch bool query** — returning highly relevant results in milliseconds.

---

## 🚀 Key Features

| Feature | Description |
|---|---|
| **NLP Query Parser** | spaCy + RapidFuzz pipeline extracts category, brand, color, gender, price range, sort intent, sale/discount intent from raw text |
| **Smart Elasticsearch Search** | Multi-match + filter + sort driven by NLP-parsed structured intent |
| **Sort Intent Routing** | "cheapest" → price ASC; "best rated" → rating DESC; "newest" → created_at DESC; "most discounted" → discount DESC |
| **Progressive Fallback Search** | 6-level filter relaxation — never drops category, progressively relaxes brand → price → discount → keyword |
| **Real-time Autocomplete** | Entity-level (brand/category) + product name prefix suggestions on every keystroke |
| **Voice Search** | Web Speech API microphone button — speak your query in English |
| **"Did You Mean?"** | Fuzzy spell-correction hints for misspelled brands and categories |
| **Live Entity Chips** | Real-time AI parsing chips show what the engine understood as you type |
| **Dual-Write Safety** | Every product write goes to MongoDB (primary) + Elasticsearch (secondary) with exponential-backoff retry and `sync_failures` collection |
| **In-Memory TTL Cache** | 2-minute cache per search query, 5-minute cache for product list — no Redis required |
| **Keep-Alive System** | Daemon thread (backend) + `useKeepAlive` hook (frontend) prevent Render free-tier cold starts |
| **User Ratings** | Submit per-product star ratings; averaged and persisted back to MongoDB + Elasticsearch |
| **Add Product Form** | Create products directly from the UI; auto-discovers synonyms via Datamuse API |
| **Filter Sidebar** | Client-side filtering by category, price range, and minimum rating |
| **Full Product Detail Page** | Breadcrumb nav, quantity picker, wishlist, share, discount badge, stock status, description tab, reviews tab, related products section |
| **Responsive Cart** | Add/remove/adjust quantity, order summary with tax calculation, checkout confirmation |
| **Render Deployment** | One-click `render.yaml` for full-stack deployment (Python web + static site) |

---

## 🧠 NLP Engine — How It Works

The core of CART is [`backend/app/utils/query_parser.py`](backend/app/utils/query_parser.py). Given a free-text query, it produces a structured intent object:

```
Query: "cheapest red Nike shoes for men under ₹3000"

Parsed: {
  "category":  "shoes",
  "brand":     "nike",
  "color":     "red",
  "gender":    "men",
  "price_max": 3000,
  "sort_by":   "price_asc",
  "keywords":  [],
  "is_sale":   false,
  "in_stock":  false,
  "min_discount": null,
  "did_you_mean": null
}
```

### Pipeline (in order):
1. **Multi-word synonym normalisation** — regex patterns map `"running shoes"` → `"shoes"`, `"earbuds"` → `"earphone"` before tokenisation
2. **Sort intent extraction** — regex detects `"cheapest"`, `"best rated"`, `"newest"`, `"most discounted"` and strips them from the query
3. **Sale / discount intent** — detects `"on sale"`, `"clearance"`, `"flash sale"`
4. **In-stock intent** — detects `"in stock"`, `"available now"`
5. **Percentage discount pattern** — `"50% off"` → `min_discount: 50`
6. **Price range extraction** — supports `₹`, `Rs`, `INR`, and natural language operators (`under`, `above`, `between`, `atleast`)
7. **spaCy tokenisation + lemmatisation** — `en_core_web_sm` model normalises word forms
8. **Entity classification** — exact → fuzzy (RapidFuzz) matching for: colour → gender → category → brand (priority order)
9. **"Did you mean?" generation** — fuzzy-corrects misspelled tokens against known brand/category lists

### Synonym System
- **Hardcoded defaults** in `SYNONYM_MAP` (e.g., `"headphones"` → `"earphone"`)
- **Auto-discovery** via Datamuse API when new products are added
- **Persisted in MongoDB** `synonyms` collection; loaded into memory on startup
- Brand typo correction built-in: `"samusng"` → `"samsung"`, `"addidas"` → `"adidas"`

---

## 🗂 Project Structure

```
CART_MINIMAL/
│
├── render.yaml                   # One-click Render deployment config
├── runtime.txt                   # Python 3.11
│
├── backend/
│   ├── main.py                   # FastAPI app, lifespan startup, keep-alive daemon thread
│   ├── requirements.txt          # Python dependencies
│   ├── seed_fast.py              # Product seeder script
│   ├── synonym.json              # Exported synonym reference
│   ├── migrate_synonyms.py       # Synonym migration utility
│   ├── data_loader.py            # Data loading helper
│   ├── es_query.py               # Standalone ES query helper
│   └── app/
│       ├── config.py             # Pydantic settings (MONGO_URI, ES_HOST, ES_INDEX)
│       ├── db.py                 # MongoDB + Elasticsearch client setup, index init
│       ├── models.py             # Pydantic schemas: ProductCreate, ProductUpdate, ProductResponse
│       ├── cache.py              # In-memory TTL cache (no Redis)
│       ├── routes/
│       │   └── product_routes.py      # All REST endpoints
│       ├── services/
│       │   └── product_service.py     # CRUD, NLP search, autocomplete, fallback, resync
│       └── utils/
│           ├── query_parser.py        # ⭐ NLP engine (spaCy + RapidFuzz)
│           └── auto_synonyms.py       # Datamuse API + curated product synonyms
│
└── frontend/
    ├── index.html
    ├── vite.config.js
    ├── tailwind.config.js
    └── src/
        ├── main.jsx
        ├── App.jsx               # Routes + providers + lazy-loading
        ├── pages/
        │   ├── Index.jsx         # Home — hero section + product grid + filter sidebar
        │   ├── Products.jsx      # Listing with filter sidebar, skeleton states, empty state
        │   ├── ProductDetail.jsx # Full PDP: image, pricing, qty picker, tabs, reviews, related
        │   ├── Cart.jsx          # Cart with qty controls, order summary, checkout toast
        │   ├── AddProduct.jsx    # Product creation form
        │   └── NotFound.jsx      # 404 page
        ├── components/
        │   ├── SmartSearchBar.jsx   # ⭐ Typewriter placeholder, autocomplete, voice, entity chips
        │   ├── Header.jsx           # Fixed nav, debounced search, cart badge, mobile menu
        │   ├── ProductCard.jsx      # Card with discount badge, rating, add-to-cart
        │   ├── ProductList.jsx      # List layout wrapper
        │   ├── FilterPanel.jsx      # Category, price range, rating filters
        │   ├── ProductForm.jsx      # Reusable product form component
        │   └── UserRating.jsx       # Star rating input component
        ├── contexts/
        │   ├── ProductsContext.jsx  # Products state, search, CRUD, rating
        │   └── CartContext.jsx      # Cart state: add, remove, qty, wishlist, checkout
        ├── hooks/
        │   ├── useDebounce.js       # Debounce hook for search inputs
        │   ├── useKeepAlive.js      # Pings /health; shows "waking up" toast on cold start
        │   ├── use-toast.js         # Toast notification hook
        │   └── use-mobile.jsx       # Responsive breakpoint hook
        └── lib/
            ├── api.js               # All API calls with timeout, mapping, error handling
            └── utils.js             # formatPrice, getAvgRating helpers
```

---

## 🌐 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | API root, NLP readiness status |
| `GET` | `/health` | Health check (used by keep-alive) |
| `GET` | `/nlp-status` | NLP engine: brand count, category count, synonym groups |
| `GET` | `/search?q=...&size=N` | NLP-powered product search |
| `GET` | `/search/meta?q=...` | Search + parsed entity metadata (chips, did_you_mean, sort_by) |
| `GET` | `/search/parse?q=...` | Parse query without executing search — entity chips only |
| `GET` | `/search/autocomplete?q=...&limit=N` | Entity + product name prefix suggestions |
| `GET` | `/products?limit=N` | All products (cached 5 min) |
| `GET` | `/products/{id}` | Single product by ID |
| `POST` | `/products` | Create new product (dual-write: MongoDB + ES) |
| `PUT` | `/products/{id}` | Update product (dual-write) |
| `DELETE` | `/products/{id}` | Delete product (dual-write) |
| `POST` | `/refresh-nlp` | Reload brands/categories from DB into NLP parser |

---

## 🛠 Local Setup

### Prerequisites
- Python 3.10+ with `pip`
- Node.js 18+
- MongoDB (local or Atlas)
- Elasticsearch 7.x (local, Bonsai.io, or Elastic Cloud)

### 1. Backend

```bash
cd backend

# Create and activate virtual environment (recommended)
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# Install dependencies + download spaCy model
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# Configure environment
# Edit .env with your actual values:
# MONGO_URI=mongodb+srv://...
# MONGO_DB=ecommerce
# ES_HOST=https://...
# ES_INDEX=products

# Start the API server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Seed the Database (First Run)

```bash
# Inside backend/ with venv active
python seed_fast.py
```

### 3. Frontend

```bash
cd frontend
npm install

# Set API URL (for local dev)
echo "VITE_API_URL=http://localhost:8000" > .env.local

npm run dev    # Opens at http://localhost:5173
```

---

## ☁️ Deployment (Render)

The [`render.yaml`](render.yaml) at the project root configures both services:

| Service | Type | Details |
|---|---|---|
| `cart-api` | Python Web Service | `uvicorn main:app`, `/health` health check |
| `cart-frontend` | Static Site | `npm run build`, SPA rewrites enabled |

Set these environment variables in the Render dashboard:
- `MONGO_URI` — MongoDB Atlas connection string
- `ES_HOST` — Elasticsearch host URL (e.g., Bonsai.io)
- `MONGO_DB` = `ecommerce`
- `ES_INDEX` = `products`

---

## 📊 Technical Concepts (Interview-Ready)

### Elasticsearch Bool Query Structure
```python
{
  "must":   [multi_match on name/description/brand/category/color],  # text relevance
  "filter": [term(category), term(brand), range(price), range(discount)],  # exact, no scoring
  "should": [term(color, boost=4.0), term(gender, boost=2.5)],  # soft boost
  "sort":   dynamic — driven by NLP sort_by field
}
```

### Progressive Fallback (6 Levels)
When 0 results found, filters are relaxed in order — **category is NEVER dropped**:
1. Full query (retry)
2. Drop brand filter
3. Drop price filter
4. Drop discount/stock filters (show all category items)
5. Use `match_all` + category (handle bad typos)
6. `match_all` everywhere (only if no category specified)

### Dual-Write with Retry
- **MongoDB** = source of truth (inserted first)
- **Elasticsearch** = search index (indexed with exponential backoff: 0.5s, 1s)
- **`sync_failures` collection** = audit log for failed ES writes, re-synced via `/refresh-nlp`

### In-Memory TTL Cache
Custom `InMemoryCache` class — no Redis, no external dependency:
- Search results: 2-minute TTL per `(query, size)` cache key (MD5 hash)
- Product list: 5-minute TTL
- Invalidated on create/update/delete

### Entity Extraction Priority
`color → gender → category (exact) → brand (exact) → category (fuzzy) → brand (fuzzy) → keyword`

This ordering prevents mis-classification — e.g., `"boat"` is never fuzzily matched to `"boots"` because brand exact-match takes priority.

---

## 👨‍💻 Author

**Harsh Kumar** — [GitHub](https://github.com/harsh07032004)

*Built as a showcase project for placements — demonstrating full-stack development, NLP, and search engineering.*
