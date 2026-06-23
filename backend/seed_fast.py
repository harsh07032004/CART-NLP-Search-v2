import random
from datetime import datetime, timedelta
import numpy as np
if not hasattr(np, 'float_'):
    np.float_ = np.float64
from app.db import product_collection, es_client, settings, init_es_index
from bson import ObjectId

RANDOM_COUNT = 700  # additional random products on top of guaranteed ones

CATEGORIES = {
    "shoes": {
        "brands": ["nike", "adidas", "puma", "reebok", "campus", "sparx", "bata", "woodland", "skechers", "converse"],
        "names": ["Running Shoes", "Sports Sneakers", "Casual Trainers", "Lifestyle Kicks", "Walking Shoes", "Training Shoes", "Classic Sneakers"],
        "base_price": (800, 8000),
    },
    "phone": {
        "brands": ["apple", "samsung", "oneplus", "xiaomi", "realme", "vivo", "oppo", "motorola"],
        "names": ["Smartphone", "Pro Max", "Ultra", "Lite Edition", "5G Phone", "Gaming Phone"],
        "base_price": (8000, 150000),
    },
    "earphone": {
        "brands": ["sony", "boat", "jbl", "noise", "oneplus", "samsung", "realme", "boult"],
        "names": ["Wireless Earbuds", "Neckband", "Over-Ear Headphones", "TWS Earphones", "Bass Boost", "Sport Earphones"],
        "base_price": (299, 18000),
    },
    "shirts": {
        "brands": ["allen solly", "peter england", "van heusen", "louis philippe", "arrow", "ucb", "levis", "h&m"],
        "names": ["Casual Shirt", "Formal Shirt", "Polo T-Shirt", "Cotton Tee", "Slim Fit Shirt", "Oxford Shirt", "Linen Shirt"],
        "base_price": (399, 4000),
    },
    "watches": {
        "brands": ["titan", "fastrack", "casio", "fossil", "sonata", "timex", "samsung", "apple"],
        "names": ["Analog Watch", "Digital Watch", "Smartwatch", "Chronograph", "Sports Watch", "Dress Watch"],
        "base_price": (800, 60000),
    },
    "laptop": {
        "brands": ["hp", "dell", "lenovo", "asus", "acer", "apple", "msi"],
        "names": ["Gaming Laptop", "Business Laptop", "Ultrabook", "Chromebook", "Workstation", "Student Laptop"],
        "base_price": (28000, 200000),
    },
    "jackets": {
        "brands": ["columbia", "the north face", "h&m", "zara", "levis", "ucb", "allen solly", "arrow", "puma", "nike"],
        "names": ["Bomber Jacket", "Denim Jacket", "Leather Jacket", "Windbreaker", "Puffer Jacket", "Hoodie", "Track Jacket", "Fleece Jacket", "Varsity Jacket"],
        "base_price": (599, 8000),
    },
    "jeans": {
        "brands": ["levis", "wrangler", "pepe jeans", "lee", "ucb", "h&m", "zara", "spykar"],
        "names": ["Slim Fit Jeans", "Skinny Jeans", "Straight Cut Jeans", "Bootcut Jeans", "Relaxed Fit Jeans", "Distressed Jeans", "Stretch Jeans"],
        "base_price": (599, 5000),
    },
    "sandals": {
        "brands": ["bata", "crocs", "paragon", "sparx", "woodland", "red tape", "adidas", "puma"],
        "names": ["Casual Sandals", "Sports Sandals", "Flip Flops", "Slides", "Outdoor Sandals", "Comfort Sandals", "Beach Slippers"],
        "base_price": (199, 3000),
    },
    "bags": {
        "brands": ["wildcraft", "american tourister", "skybags", "safari", "f gear", "fastrack", "caprese", "lavie"],
        "names": ["Backpack", "Tote Bag", "Laptop Bag", "Messenger Bag", "Duffel Bag", "Sling Bag", "Shoulder Bag", "Travel Bag"],
        "base_price": (499, 6000),
    },
}

ADJECTIVES = ["Premium", "Classic", "Pro", "Max", "Ultra", "Lite", "Elite", "Sport", "Air", "Flex", "Neo", "X", "Signature", "Essential"]
COLORS = ["black", "white", "blue", "red", "silver", "gold", "grey", "navy", "green", "brown"]
GENDERS = ["men", "women", "unisex"]

IMAGE_URLS = {
    "shoes": [
        "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400",
        "https://images.unsplash.com/photo-1606107557195-0e29a4b5b4aa?w=400",
        "https://images.unsplash.com/photo-1595950653106-6c9ebd614d3a?w=400",
        "https://images.unsplash.com/photo-1600185365926-3a2ce3cdb9eb?w=400",
        "https://images.unsplash.com/photo-1549298916-b41d501d3772?w=400",
    ],
    "phone": [
        "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=400",
        "https://images.unsplash.com/photo-1592899677977-9c10ca588bbd?w=400",
        "https://images.unsplash.com/photo-1598327105666-5b89351aff97?w=400",
        "https://images.unsplash.com/photo-1605236453806-6ff36851218e?w=400",
    ],
    "earphone": [
        "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400",
        "https://images.unsplash.com/photo-1484704849700-f032a568e944?w=400",
        "https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=400",
        "https://images.unsplash.com/photo-1583394838336-acd977736f90?w=400",
    ],
    "shirts": [
        "https://images.unsplash.com/photo-1596755094514-f87e34085b2c?w=400",
        "https://images.unsplash.com/photo-1602810318383-e386cc2a3ccf?w=400",
        "https://images.unsplash.com/photo-1598033129183-c4f50c736f10?w=400",
        "https://images.unsplash.com/photo-1620799140408-edc6dcb6d633?w=400",
    ],
    "watches": [
        "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400",
        "https://images.unsplash.com/photo-1524592094714-0f0654e20314?w=400",
        "https://images.unsplash.com/photo-1546868871-7041f2a55e12?w=400",
        "https://images.unsplash.com/photo-1533139502658-0198f920d8e8?w=400",
    ],
    "laptop": [
        "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=400",
        "https://images.unsplash.com/photo-1525547719571-a2d4ac8945e2?w=400",
        "https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?w=400",
        "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=400",
    ],
    "jackets": [
        "https://images.unsplash.com/photo-1551698618-1dfe5d97d256?w=400",
        "https://images.unsplash.com/photo-1544022613-e87ca75a784a?w=400",
        "https://images.unsplash.com/photo-1591047139829-d91aecb6caea?w=400",
        "https://images.unsplash.com/photo-1521223890158-f9f7c3d5d504?w=400",
    ],
    "jeans": [
        "https://images.unsplash.com/photo-1542272454315-4c01d7abdf4a?w=400",
        "https://images.unsplash.com/photo-1582552938357-32b906df40cb?w=400",
        "https://images.unsplash.com/photo-1555689502-c4b22d76c56f?w=400",
        "https://images.unsplash.com/photo-1604176354204-9268737828e4?w=400",
    ],
    "sandals": [
        "https://images.unsplash.com/photo-1603487742131-4160ec999306?w=400",
        "https://images.unsplash.com/photo-1565814329452-e1efa11c5b89?w=400",
        "https://images.unsplash.com/photo-1519415510236-718bdfcd89c8?w=400",
        "https://images.unsplash.com/photo-1531310197839-ccf54634509e?w=400",
    ],
    "bags": [
        "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=400",
        "https://images.unsplash.com/photo-1548036328-c9fa89d128fa?w=400",
        "https://images.unsplash.com/photo-1590874103328-eac38a683ce7?w=400",
        "https://images.unsplash.com/photo-1547949003-9792a18a2601?w=400",
    ],
}


def generate_ratings():
    num_ratings = random.randint(3, 12)
    ratings = []
    for _ in range(num_ratings):
        rating = random.choices([1, 2, 3, 4, 5], weights=[4, 8, 18, 35, 35])[0]
        ratings.append({
            "userId": f"user{random.randint(1000, 9999)}",
            "rating": rating,
            "timestamp": (datetime.utcnow() - timedelta(days=random.randint(1, 180))).isoformat(),
        })
    return ratings


def _discount(weights=(30, 30, 25, 15)):
    """Generate a discount value with given weight distribution: 0, 10-25%, 25-50%, 50-70%."""
    bucket = random.choices([0, 1, 2, 3], weights=weights)[0]
    if bucket == 0:
        return 0
    elif bucket == 1:
        return random.randint(10, 25)
    elif bucket == 2:
        return random.randint(25, 50)
    else:
        return random.randint(50, 70)


def generate_product(cat_key=None, brand=None, color=None, gender=None, price=None, discount=None):
    if cat_key is None:
        cat_key = random.choice(list(CATEGORIES.keys()))
    cat_data = CATEGORIES[cat_key]

    if brand is None:
        brand = random.choice(cat_data["brands"])
    name_base = random.choice(cat_data["names"])
    adjective = random.choice(ADJECTIVES)
    if color is None:
        color = random.choice(COLORS)
    if gender is None:
        gender = random.choice(GENDERS)

    name = f"{brand.title()} {adjective} {name_base}"
    if random.random() > 0.5:
        name += f" {random.randint(1, 99)}"

    description = f"{name} - Perfect for {gender}. Available in {color}. Category: {cat_key}."
    if cat_key in ["phone", "earphone", "laptop", "watches"]:
        description += " Electronics & gadgets."

    price_range = cat_data["base_price"]
    if price is None:
        price = random.randint(price_range[0], price_range[1])

    if discount is None:
        discount = _discount()

    stock = random.randint(0, 300)

    return {
        "name": name,
        "description": description,
        "category": cat_key,
        "brand": brand,
        "price": price,
        "image_url": random.choice(IMAGE_URLS[cat_key]),
        "gender": gender,
        "color": color,
        "discount": discount,
        "stock": stock,
        "userRatings": generate_ratings(),
        "created_at": datetime.utcnow().isoformat(),
    }


def generate_guaranteed_products():
    """
    Guaranteed coverage matrix: every key brand × color × gender × price bucket.
    Ensures common queries ALWAYS find exact matches without needing fallback.
    """
    guaranteed = []

    # ── SHOES ──
    for brand in ["nike", "adidas", "puma", "reebok", "campus"]:
        for price in [999, 1499, 1999, 2499, 2999, 3999, 5999]:
            for color in ["red", "black", "white", "blue", "grey"]:
                for gender in ["men", "women"]:
                    # Sale items explicitly flagged
                    disc = _discount(weights=[20, 25, 35, 20]) if price < 3000 else _discount()
                    guaranteed.append(generate_product("shoes", brand, color, gender, price, disc))

    # ── JACKETS ── (ensure many discounted ones exist)
    for brand in ["columbia", "h&m", "levis", "ucb", "puma", "nike", "allen solly", "zara"]:
        for price in [599, 999, 1499, 1999, 2999, 4999]:
            for color in ["black", "blue", "grey", "navy", "red", "brown"]:
                for gender in ["men", "women", "unisex"]:
                    # Higher sale probability for jackets (clearance sales are common)
                    disc = _discount(weights=[15, 20, 35, 30])
                    guaranteed.append(generate_product("jackets", brand, color, gender, price, disc))

    # ── JEANS ──
    for brand in ["levis", "wrangler", "pepe jeans", "lee", "ucb", "h&m"]:
        for price in [799, 1299, 1799, 2499, 3499]:
            for color in ["blue", "black", "grey", "navy"]:
                for gender in ["men", "women"]:
                    guaranteed.append(generate_product("jeans", brand, color, gender, price))

    # ── SHIRTS ──
    for brand in ["allen solly", "peter england", "van heusen", "ucb", "arrow", "levis"]:
        for price in [399, 699, 999, 1499, 1999, 2499]:
            for color in ["white", "blue", "black", "grey", "red"]:
                for gender in ["men", "women"]:
                    guaranteed.append(generate_product("shirts", brand, color, gender, price))

    # ── PHONES ──
    for brand in ["samsung", "xiaomi", "realme", "oneplus", "vivo", "oppo", "motorola"]:
        for price in [7999, 10999, 13999, 17999, 24999, 34999]:
            guaranteed.append(generate_product("phone", brand, random.choice(COLORS), random.choice(GENDERS), price))
    for price in [79999, 99999, 129999]:  # Apple
        for color in ["black", "white", "silver", "gold"]:
            guaranteed.append(generate_product("phone", "apple", color, "unisex", price))

    # ── EARPHONES ──
    for brand in ["boat", "boult", "noise", "jbl", "sony"]:
        for price in [299, 499, 799, 1299, 1999, 2999]:
            for color in ["black", "white", "blue", "red"]:
                disc = _discount(weights=[25, 30, 30, 15])
                guaranteed.append(generate_product("earphone", brand, color, random.choice(GENDERS), price, disc))

    # ── WATCHES ──
    for brand in ["titan", "fastrack", "casio", "fossil", "sonata"]:
        for price in [800, 1500, 2500, 4500, 8000, 15000]:
            for color in ["black", "silver", "gold", "blue", "brown"]:
                for gender in ["men", "women"]:
                    guaranteed.append(generate_product("watches", brand, color, gender, price))

    # ── LAPTOPS ──
    for brand in ["hp", "dell", "lenovo", "asus", "acer"]:
        for price in [28000, 40000, 55000, 70000, 90000]:
            for color in ["black", "silver", "grey"]:
                guaranteed.append(generate_product("laptop", brand, color, "unisex", price))
    for price in [99999, 129999, 159999]:  # Apple MacBooks
        guaranteed.append(generate_product("laptop", "apple", "silver", "unisex", price))

    # ── SANDALS ──
    for brand in ["bata", "crocs", "sparx", "paragon", "adidas"]:
        for price in [199, 399, 699, 999, 1499]:
            for color in ["black", "white", "blue", "brown"]:
                for gender in ["men", "women", "unisex"]:
                    guaranteed.append(generate_product("sandals", brand, color, gender, price))

    # ── BAGS ──
    for brand in ["wildcraft", "american tourister", "skybags", "safari", "fastrack"]:
        for price in [599, 999, 1499, 2499, 3999]:
            for color in ["black", "blue", "grey", "red"]:
                for gender in ["men", "women", "unisex"]:
                    guaranteed.append(generate_product("bags", brand, color, gender, price))

    return guaranteed


def seed():
    print(f"\n{'='*55}")
    print("SEEDING WITH FULL COVERAGE (Guaranteed + Random)")
    print(f"{'='*55}\n")

    print("Clearing existing products...")
    product_collection.delete_many({})
    try:
        es_client.indices.delete(index=settings.ES_INDEX, ignore=[400, 404])
        print(f"Deleted index '{settings.ES_INDEX}'")
    except Exception as e:
        print(f"Index delete error: {e}")

    init_es_index()

    guaranteed = generate_guaranteed_products()
    print(f"Generated {len(guaranteed)} guaranteed coverage products")

    print(f"Generating {RANDOM_COUNT} additional random products...")
    random_products = [generate_product() for _ in range(RANDOM_COUNT)]

    products = guaranteed + random_products
    total = len(products)
    print(f"Total products: {total}")

    # ── MongoDB bulk insert ──
    result = product_collection.insert_many(products)
    print(f"Inserted {len(result.inserted_ids)} products into MongoDB")

    # ── Elasticsearch bulk index ──
    print("Indexing to Elasticsearch...")
    bulk_body = []
    for product in products:
        doc_id = str(product["_id"]) if "_id" in product else str(ObjectId())
        bulk_body.append({"index": {"_index": settings.ES_INDEX, "_id": doc_id}})
        es_doc = {k: v for k, v in product.items() if k != "_id"}
        bulk_body.append(es_doc)

    response = es_client.bulk(body=bulk_body)
    errors = response.get("errors", False)
    print(f"Elasticsearch bulk index done. Errors: {errors}")

    if errors:
        failed = [item for item in response["items"] if "error" in item.get("index", {})]
        print(f"  {len(failed)} failed items (first): {failed[:2]}")

    print(f"\n{'='*55}")
    print(f"SEEDING COMPLETE — {total} products added.")
    breakdown = {}
    for p in products:
        breakdown[p["category"]] = breakdown.get(p["category"], 0) + 1
    for cat, cnt in sorted(breakdown.items()):
        print(f"  {cat:<12} {cnt:>5} products")
    print(f"{'='*55}")


if __name__ == "__main__":
    seed()
