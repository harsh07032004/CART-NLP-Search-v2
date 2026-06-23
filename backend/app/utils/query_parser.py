import spacy
import re
import json
from rapidfuzz import process, fuzz

nlp = spacy.load("en_core_web_sm")

# ---------------------------------------------------------------------------
# Synonym Map — loaded from MongoDB on startup, seeded with sensible defaults
# ---------------------------------------------------------------------------
SYNONYM_MAP = {
    "categories": {
        "shoes": ["footwear", "sneakers", "kicks", "trainers", "runners", "sports shoes",
                  "running shoes", "shoe", "joggers", "loafers"],
        "shirts": ["shirt", "tshirt", "t-shirt", "top", "tee", "polo",
                   "formal shirt", "casual shirt", "blouse", "jersey"],
        "phone": ["mobile", "smartphone", "cellphone", "handset", "iphone", "android",
                  "phones", "mobiles", "smartphones"],
        "earphone": ["earphones", "earbuds", "headphones", "headset", "airpods",
                     "tws", "wireless earbuds", "earpiece", "in-ear"],
        "laptop": ["laptops", "notebook", "computer", "macbook", "chromebook",
                   "ultrabook", "notebooks"],
        "watches": ["watch", "smartwatch", "wristwatch", "timepiece", "fitness band",
                    "fitness tracker", "smart band"],
        "bags": ["bag", "backpack", "purse", "handbag", "tote", "satchel", "clutch"],
        "jeans": ["denim", "denims", "jeans pants"],
        "jackets": ["jacket", "hoodie", "sweatshirt", "coat", "blazer"],
        "sandals": ["sandal", "flip flops", "slippers", "chappal", "chappals"],
    },
    "brands": {
        "nike": ["nikes", "nke"],
        "adidas": ["addidas", "adiddas", "adidass"],
        "samsung": ["samung", "samsng", "samusng"],
        "apple": ["iphone", "macbook", "airpods"],
        "oneplus": ["one plus", "1+", "1 plus"],
        "xiaomi": ["mi", "redmi", "poco"],
        "boat": ["b0at", "b-oat"],
        "hp": ["hewlett packard", "hewlett-packard"],
        "lenovo": ["lenvo", "lenovoo"],
        "sony": ["snoy", "soony"],
    }
}

# Multi-word synonym normalisation (applied before tokenisation)
MULTIWORD_SYNONYM_PATTERNS = [
    (r"smart\s*phones?", "phone"),
    (r"running\s*shoes?", "shoes"),
    (r"sports?\s*shoes?", "shoes"),
    (r"t-?shirts?", "shirts"),
    (r"ear\s*phones?", "earphone"),
    (r"ear\s*buds?", "earphone"),
    (r"head\s*phones?", "earphone"),
    (r"wrist\s*watch", "watches"),
    (r"smart\s*watch", "watches"),
    (r"lap\s*top", "laptop"),
    (r"back\s*pack", "bags"),
    (r"hand\s*bag", "bags"),
    (r"flip\s*flops?", "sandals"),
]

# ---------------------------------------------------------------------------
# Sort Intent Patterns — matched before tokenisation
# ---------------------------------------------------------------------------
SORT_INTENT_PATTERNS = {
    "price_asc": [
        r"\b(cheap(?:est)?|lowest\s+price|most\s+affordable|least\s+expensive|"
        r"budget(?:\s+friendly)?|economical|inexpensive)\b"
    ],
    "price_desc": [
        r"\b(most\s+expensive|high(?:est)?\s+price|premium|luxury|"
        r"high[- ]?end|costl(?:y|ier))\b"
    ],
    "rating_desc": [
        r"\b(best\s+rated|top[- ]rated|highest[- ]rated|most\s+popular|"
        r"top\s+pick|best\s+seller|highly\s+rated|most\s+reviewed)\b"
    ],
    "discount_desc": [
        r"\b(most\s+discounted|best\s+deal|best\s+offer|highest\s+discount|"
        r"biggest\s+deal|max(?:imum)?\s+discount)\b"
    ],
    "newest": [
        r"\b(new(?:est)?|latest|fresh|just\s+arrived|new\s+arrival(?:s)?|trending)\b"
    ],
}

# Sale / offer intent
SALE_PATTERN = (
    r"\b(sale|discounted|on\s+sale|on\s+offer|clearance|deal(?:s)?|"
    r"offer(?:s)?|\d+\s*%\s*off|flash\s*sale)\b"
)

# In-stock intent
STOCK_PATTERN = r"\b(in\s+stock|available|ready\s+to\s+ship|available\s+now)\b"

# Words that should NEVER be treated as entity tokens
STOP_WORDS = {
    "suggest", "show", "tell", "find", "give", "want", "need", "looking",
    "for", "me", "i", "a", "an", "the", "some", "this", "thsi", "search",
    "please", "can", "you", "best", "good", "nice", "great", "suggested",
    "suggestion", "buy", "get", "order", "purchase", "under", "below",
    "above", "over", "between", "and", "or", "with", "at", "in", "on",
    "rs", "inr", "rupee", "rupees", "upto", "price", "cost", "worth",
    "around", "approximately", "cheap", "affordable", "budget", "premium",
    # Sale / intent words — don't leak into ES must clause
    "sale", "offer", "offers", "deal", "deals", "discount", "discounted",
    "clearance", "off", "percent", "flash",
    # Stock intent words
    "stock", "available", "availability", "now", "ready",
    # Misc noise
    "any", "all", "more", "less", "most", "least", "very", "much",
}

# Colours (extended)
COLORS = [
    "red", "blue", "black", "white", "green", "yellow", "pink", "brown",
    "grey", "gray", "orange", "purple", "silver", "gold", "navy", "maroon",
    "beige", "cream", "olive", "violet", "magenta", "cyan", "turquoise",
    "coral", "lavender", "teal", "indigo", "khaki", "charcoal",
]

# Gender tokens — checked BEFORE fuzzy brand matching to avoid mis-matches
GENDERS = ["men", "women", "boys", "girls", "unisex", "male", "female",
           "mens", "womens", "kids", "children", "child", "man", "woman"]

# Canonical brand list
BRANDS = [
    "nike", "adidas", "puma", "reebok", "campus", "sparx", "bata", "woodland",
    "apple", "samsung", "oneplus", "xiaomi", "realme", "vivo", "oppo", "motorola",
    "sony", "boat", "jbl", "noise", "boult",
    "allen solly", "peter england", "van heusen", "louis philippe", "arrow", "ucb",
    "titan", "fastrack", "casio", "fossil", "sonata", "timex",
    "hp", "dell", "lenovo", "asus", "acer", "msi",
    "skechers", "new balance", "asics", "fila", "converse", "vans",
    "red tape", "h&m", "zara", "crocs", "levis", "levi's",
]

# Canonical category list
RAW_CATEGORIES = [
    "shoes", "phone", "earphone", "shirts", "watches", "laptop",
    "sandals", "boots", "heels", "flats", "slippers", "sneakers",
    "pants", "jeans", "jackets", "dresses",
    "mobile", "smartphone", "tablet", "camera",
    "bags", "wallets", "belts",
]

# Price patterns — support ₹, Rs, INR prefixes and word-based operators
PRICE_PATTERNS = [
    (r"between\s*[₹$rs]*\s*(\d+)\s*(?:and|to|-)\s*[₹$rs]*\s*(\d+)", "between"),
    (r"(?:under|below|less\s*than)\s*[₹$rs]*\s*(\d+)", "<"),
    (r"(?:above|over|greater\s*than|more\s*than)\s*[₹$rs]*\s*(\d+)", ">"),
    (r"(?:upto|up\s*to|atmost|at\s*most)\s*[₹$rs]*\s*(\d+)", "<="),
    (r"(?:atleast|at\s*least|minimum|min)\s*[₹$rs]*\s*(\d+)", ">="),
    # Bare ₹/Rs prefix: "₹5000", "Rs 2000"
    (r"[₹]\s*(\d+)", "<="),
    (r"\brs\.?\s*(\d+)", "<="),
]

# Discount-specific price patterns: "50% off", "20 percent discount"
DISCOUNT_PATTERN = r"\b(\d{1,2})\s*(?:%|percent(?:age)?)\s*(?:off|discount)\b"

# ---------------------------------------------------------------------------
# Entity knowledge base helpers
# ---------------------------------------------------------------------------

def _lemmatize_list(word_list):
    return list(set(token.lemma_ for token in nlp(" ".join(word_list))))


CATEGORIES = _lemmatize_list(RAW_CATEGORIES)


def update_entities(new_brands=None, new_categories=None):
    global BRANDS, RAW_CATEGORIES, CATEGORIES
    if new_brands:
        normalized = [b.lower().strip() for b in new_brands if b]
        BRANDS = list(set(BRANDS + normalized))
    if new_categories:
        normalized = [c.lower().strip() for c in new_categories if c]
        RAW_CATEGORIES = list(set(RAW_CATEGORIES + normalized))
        CATEGORIES = _lemmatize_list(RAW_CATEGORIES)


def add_synonyms(field: str, key: str, new_synonyms: list):
    from app.db import synonym_collection

    if field not in SYNONYM_MAP:
        SYNONYM_MAP[field] = {}

    key = key.lower()
    current = SYNONYM_MAP[field].get(key, [])
    updated = list(set(current + [s.lower() for s in new_synonyms]))

    if len(updated) > len(current):
        SYNONYM_MAP[field][key] = updated
        try:
            synonym_collection.update_one(
                {"_id": field},
                {"$addToSet": {f"data.{key}": {"$each": [s.lower() for s in new_synonyms]}}},
                upsert=True,
            )
        except Exception as e:
            print(f"Failed to persist synonyms: {e}")


def load_synonyms_from_db():
    from app.db import synonym_collection
    try:
        for doc in synonym_collection.find({}):
            _id = doc["_id"]
            data = doc.get("data", {})
            # Merge (don't overwrite hardcoded defaults)
            for k, v in data.items():
                existing = SYNONYM_MAP.get(_id, {}).get(k, [])
                SYNONYM_MAP.setdefault(_id, {})[k] = list(set(existing + v))
        print(f"Synonyms loaded from DB for: {list(SYNONYM_MAP.keys())}")
    except Exception as e:
        print(f"Error loading synonyms from DB: {e}")


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------

def _fuzzy_match(token: str, choices: list, threshold: int = 72) -> str | None:
    if not choices or not token:
        return None
    result = process.extractOne(token, choices, scorer=fuzz.ratio)
    if result and result[1] >= threshold:
        return result[0]
    return None


def _resolve_synonym(token: str) -> str:
    """Replace token with canonical key if it appears in any synonym list."""
    for field in ("categories", "brands"):
        if field not in SYNONYM_MAP:
            continue
        for key, synonyms in SYNONYM_MAP[field].items():
            if token in synonyms:
                return key
    return token


def _apply_multiword_synonyms(query: str) -> str:
    for pattern, replacement in MULTIWORD_SYNONYM_PATTERNS:
        query = re.sub(pattern, replacement, query, flags=re.IGNORECASE)
    return query


def _extract_sort_intent(query: str) -> tuple[str | None, str]:
    """Detect sort intent and strip those words from the query.
    Returns (sort_by, cleaned_query)."""
    for sort_key, patterns in SORT_INTENT_PATTERNS.items():
        for pattern in patterns:
            m = re.search(pattern, query, re.IGNORECASE)
            if m:
                cleaned = query[: m.start()].rstrip() + " " + query[m.end():].lstrip()
                return sort_key, cleaned.strip()
    return None, query


def get_spelling_suggestion(token: str) -> str | None:
    """Return a spelling suggestion for a misspelled brand or category token."""
    # Check brands first
    brand_match = _fuzzy_match(token, BRANDS, threshold=60)
    if brand_match and brand_match != token:
        return brand_match
    # Then categories
    cat_match = _fuzzy_match(token, RAW_CATEGORIES, threshold=60)
    if cat_match and cat_match != token:
        return cat_match
    return None


def build_did_you_mean(original_query: str, parsed: dict) -> str | None:
    """If the parsed result found entities via fuzzy matching, build a
    'Did you mean …?' suggestion string to show the user."""
    corrections = []
    tokens = original_query.lower().split()
    for token in tokens:
        if len(token) < 3:
            continue
        suggestion = get_spelling_suggestion(token)
        if suggestion and suggestion.lower() != token.lower():
            corrections.append((token, suggestion))

    if not corrections:
        return None

    result = original_query
    for original, corrected in corrections:
        result = re.sub(re.escape(original), corrected, result, flags=re.IGNORECASE)
    return result if result.lower() != original_query.lower() else None


# ---------------------------------------------------------------------------
# Main parser
# ---------------------------------------------------------------------------

def parse_query(query: str) -> dict:
    raw_query = query.lower().strip()
    query = _apply_multiword_synonyms(raw_query)

    result = {
        "keywords": [],
        "category": None,
        "brand": None,
        "color": None,
        "gender": None,
        "price_min": None,
        "price_max": None,
        # NEW fields
        "sort_by": None,
        "is_sale": False,
        "in_stock": False,
        "min_discount": None,
        "did_you_mean": None,
    }

    # ---- 0. Sort intent (before price, so "cheapest" doesn't get swallowed) ----
    sort_intent, query = _extract_sort_intent(query)
    result["sort_by"] = sort_intent

    # Map price_asc sort to also imply "show cheapest" — don't set price_max
    # (just influence ES sort order later)

    # ---- 0.5 Sale / discount intent ----
    if re.search(SALE_PATTERN, query, re.IGNORECASE):
        result["is_sale"] = True

    # ---- 0.6 In-stock intent ----
    if re.search(STOCK_PATTERN, query, re.IGNORECASE):
        result["in_stock"] = True

    # ---- 0.7 Percentage discount pattern: "50% off" ----
    disc_match = re.search(DISCOUNT_PATTERN, query, re.IGNORECASE)
    if disc_match:
        result["min_discount"] = int(disc_match.group(1))
        query = query[: disc_match.start()] + query[disc_match.end():]

    # ---- 1. Extract price ranges first (regex, before spaCy tokenisation) ----
    for pattern, op in PRICE_PATTERNS:
        m = re.search(pattern, query)
        if m:
            if op == "between":
                result["price_min"] = int(m.group(1))
                result["price_max"] = int(m.group(2))
            else:
                val = int(m.group(1))
                if op in ("<", "<="):
                    result["price_max"] = val
                elif op in (">", ">="):
                    result["price_min"] = val
            # Remove matched price text so it doesn't pollute keywords
            query = query[: m.start()] + query[m.end():]
            break

    doc = nlp(query)
    used_tokens = set()  # track which token indices have been consumed

    for i, token in enumerate(doc):
        if i in used_tokens:
            continue

        raw = token.text.lower()
        lemma = token.lemma_.lower()

        # Skip punctuation, numbers, stop words
        if token.is_punct or token.like_num or raw in STOP_WORDS or token.is_space:
            continue

        norm = _resolve_synonym(raw)
        norm_lemma = _resolve_synonym(lemma)

        # ---- 2. Color (exact) ----
        if result["color"] is None:
            if norm in COLORS or norm_lemma in COLORS:
                result["color"] = norm if norm in COLORS else norm_lemma
                used_tokens.add(i)
                continue
            col = _fuzzy_match(norm, COLORS, threshold=85)  # tight — avoid 'god'→'gold'
            if col:
                result["color"] = col
                used_tokens.add(i) 
                continue

        # ---- 3. Gender (exact, STRICTLY before brand fuzzy) ----
        if result["gender"] is None:
            if norm in GENDERS or norm_lemma in GENDERS:
                gender_map = {
                    "man": "men", "male": "men",
                    "woman": "women", "female": "women",
                    "child": "kids", "children": "kids",
                    "boys": "men", "girls": "women",
                }
                g = norm if norm in GENDERS else norm_lemma
                result["gender"] = gender_map.get(g, g)
                used_tokens.add(i)
                continue

        # ---- 4. Category ----
        if result["category"] is None:
            # Direct match against raw categories (exact only at this point)
            if norm in RAW_CATEGORIES:
                result["category"] = norm
                used_tokens.add(i)
                continue
            if norm_lemma in RAW_CATEGORIES:
                result["category"] = norm_lemma
                used_tokens.add(i)
                continue

            # Lemma-level exact match
            cat_lemma = nlp(norm)[0].lemma_
            cat_matched = False
            for raw_cat in RAW_CATEGORIES:
                if nlp(raw_cat)[0].lemma_ == cat_lemma:
                    result["category"] = raw_cat
                    used_tokens.add(i)
                    cat_matched = True
                    break
            if cat_matched:
                continue

        # ---- 5. Brand — EXACT match comes before fuzzy category ----
        # This ensures known brand tokens (e.g. "boat") are never mis-classified
        # as a fuzzy category match (e.g. "boots").
        if result["brand"] is None:
            if norm in BRANDS:
                result["brand"] = norm
                used_tokens.add(i)
                continue

        # ---- 4b. Fuzzy category (only if not an exact brand) ----
        if result["category"] is None and result["brand"] is None:
            cat_lemma = nlp(norm)[0].lemma_
            # Raise threshold to 80 to avoid false positives like boat→boots
            fuzzy_cat_lemma = _fuzzy_match(cat_lemma, CATEGORIES, threshold=80)
            if fuzzy_cat_lemma:
                for raw_cat in RAW_CATEGORIES:
                    if nlp(raw_cat)[0].lemma_ == fuzzy_cat_lemma:
                        result["category"] = raw_cat
                        used_tokens.add(i)
                        break
                if result["category"]:
                    continue

        # ---- 5b. Fuzzy brand (for typos like "nikey", "addidas") ----
        if result["brand"] is None:
            br = _fuzzy_match(norm, BRANDS, threshold=72)
            if br:
                result["brand"] = br
                used_tokens.add(i)
                continue

        # ---- 6. Residual keyword ----
        if raw not in STOP_WORDS and len(raw) > 1 and not token.is_stop:
            result["keywords"].append(lemma if lemma else raw)

    # Deduplicate keywords and remove any that match resolved entities
    resolved_entities = {
        result["category"], result["brand"], result["color"], result["gender"]
    } - {None}

    seen = set()
    clean_kw = []
    for kw in result["keywords"]:
        if kw not in seen and kw not in resolved_entities and kw not in STOP_WORDS:
            seen.add(kw)
            clean_kw.append(kw)
    result["keywords"] = clean_kw

    # ---- 7. Did-you-mean (spelling hint for frontend) ----
    result["did_you_mean"] = build_did_you_mean(raw_query, result)

    return result


# ---------------------------------------------------------------------------
# Autocomplete helper — returns prefix suggestions from entity lists
# ---------------------------------------------------------------------------

def get_autocomplete_suggestions(prefix: str, limit: int = 5) -> list[dict]:
    """Return structured autocomplete suggestions based on a partial query prefix.
    Each suggestion has a `text` and `type` (brand | category | query)."""
    prefix = prefix.lower().strip()
    if len(prefix) < 1:
        return []

    suggestions = []
    seen = set()

    # 1. Category matches
    for cat in RAW_CATEGORIES:
        if cat.startswith(prefix) and cat not in seen:
            suggestions.append({"text": cat, "type": "category"})
            seen.add(cat)

    # 2. Brand matches
    for brand in BRANDS:
        if brand.startswith(prefix) and brand not in seen:
            suggestions.append({"text": brand, "type": "brand"})
            seen.add(brand)

    # 3. Fuzzy fallbacks if not enough results
    if len(suggestions) < limit:
        fuzzy_cats = process.extract(prefix, RAW_CATEGORIES, scorer=fuzz.partial_ratio, limit=limit)
        for cat, score, _ in fuzzy_cats:
            if score >= 60 and cat not in seen:
                suggestions.append({"text": cat, "type": "category"})
                seen.add(cat)

        fuzzy_brands = process.extract(prefix, BRANDS, scorer=fuzz.partial_ratio, limit=limit)
        for brand, score, _ in fuzzy_brands:
            if score >= 60 and brand not in seen:
                suggestions.append({"text": brand, "type": "brand"})
                seen.add(brand)

    return suggestions[:limit]


# ---------------------------------------------------------------------------
# Standalone test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    test_queries = [
        "red nike shoes for men under 3000",
        "sheos for men",                      # typo
        "earbuds below ₹500",                 # rupee symbol
        "smartphone under Rs 15000",           # Rs prefix
        "blue laptop for women between 40000 and 80000",
        "suggest me some good watches",
        "cheapest adidas shoes",               # sort intent
        "best rated samsung phones",           # sort intent
        "50% off jackets",                     # discount intent
        "latest earphones on sale",            # sale + newest
        "samusng phone",                       # typo → did_you_mean
        "boat earphones in stock",             # in_stock
    ]
    for q in test_queries:
        print(f"\nQuery : {q}")
        print(f"Parsed: {json.dumps(parse_query(q), default=str)}")

