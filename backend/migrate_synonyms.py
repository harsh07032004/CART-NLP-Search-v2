import json
import os
from app.db import synonym_collection

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SYNONYM_PATH = os.path.join(BASE_DIR, "synonym.json")

def migrate():
    if not os.path.exists(SYNONYM_PATH):
        print("No synonym.json found.")
        return

    with open(SYNONYM_PATH, "r") as f:
        data = json.load(f)

    # Insert Categories
    if "categories" in data:
        print("Migrating categories...")
        synonym_collection.update_one(
            {"_id": "categories"},
            {"$set": {"data": data["categories"]}},
            upsert=True
        )

    # Insert Brands
    if "brands" in data:
        print("Migrating brands...")
        synonym_collection.update_one(
            {"_id": "brands"},
            {"$set": {"data": data["brands"]}},
            upsert=True
        )
        
    # Insert Colors, Genders if exist
    for key in ["colors", "genders"]:
        if key in data:
             print(f"Migrating {key}...")
             synonym_collection.update_one(
                {"_id": key},
                {"$set": {"data": data[key]}},
                upsert=True
            )

    print("Migration to MongoDB complete.")

if __name__ == "__main__":
    migrate()
