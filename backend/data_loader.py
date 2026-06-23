# data_loader.py
from dotenv import load_dotenv
import os
from pymongo import MongoClient
from elasticsearch import Elasticsearch

def load_and_index():
    load_dotenv()  # Load environment variables from .env

    mongo_uri = os.getenv("MONGO_URI")
    mongo_db = os.getenv("MONGO_DB")
    es_host = os.getenv("ES_HOST")
    es_index = os.getenv("ES_INDEX")
    


    print(f"[INFO] Connecting to MongoDB at {mongo_uri}, database: {mongo_db}")
    mongo_client = MongoClient(mongo_uri)
    db = mongo_client[mongo_db]
    collection = db.products  # Update if your collection is named differently

    print(f"[INFO] Connecting to Elasticsearch at {es_host}")
    es = Elasticsearch(es_host)

    products = list(collection.find())
    print(f"[INFO] Found {len(products)} product(s) in MongoDB.\n")

    for idx, prod in enumerate(products, 1):
        doc = {
            "name": prod.get("name", prod.get("title", "")),  # Fallback to 'title' if 'name' missing
            "description": prod.get("description", ""),
            "category": prod.get("category", "").lower(),
            "brand": prod.get("brand", "").lower(),
            "color": prod.get("color", "").lower(),
            "gender": prod.get("gender", "").lower(),
            "price": int(prod.get("price", 0)),
            "rating": float(prod.get("rating", 0.0)),
            "stock": int(prod.get("stock", 0)),
            "discount": int(prod.get("discount", 0))
        }

        print(f"[{idx}/{len(products)}] Indexing product _id={prod.get('_id')} → name={doc.get('name')}")

        try:
            res = es.index(index=es_index, id=str(prod["_id"]), body=doc)

            if res.get("result") in ("created", "updated"):
                print("  ✔ Indexed successfully")
            else:
                print(f"  ✖ Indexing failed: {res}")
        except Exception as e:
            print(f"  ❌ Exception occurred: {e}")

    print("\n✅ Data indexing complete.\n")

if __name__ == "__main__":
    load_and_index()
