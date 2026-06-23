from pymongo import MongoClient
from elasticsearch import Elasticsearch
from app.config import settings
import numpy as np
if not hasattr(np, 'float_'):
    np.float_ = np.float64

# MongoDB
mongo_client = MongoClient(settings.MONGO_URI)
db = mongo_client[settings.MONGO_DB]
product_collection = db["products"]
synonym_collection = db["synonyms"]

# Elasticsearch
es_client = Elasticsearch(settings.ES_HOST)

def init_es_index():
    """Ensures the Elasticsearch index exists with proper mapping."""
    if not es_client.indices.exists(index=settings.ES_INDEX):
        try:
            es_client.indices.create(
                index=settings.ES_INDEX,
                body={
                    "mappings": {
                        "properties": {
                            "name": {"type": "text"},
                            "description": {"type": "text"},
                            "category": {"type": "keyword"},
                            "brand": {"type": "keyword"},
                            "price": {"type": "float"},
                            "image_url": {"type": "keyword"},
                            "created_at": {"type": "date"},
                            "rating": {"type": "float"},
                            "discount": {"type": "integer"},
                            "stock": {"type": "integer"},
                            "color": {"type": "keyword"},
                            "gender": {"type": "keyword"}
                        }
                    }
                }
            )
            print(f"Index '{settings.ES_INDEX}' created.")
        except Exception as e:
            print(f"Error creating index: {e}")
    else:
        print(f"Index '{settings.ES_INDEX}' already exists.")

