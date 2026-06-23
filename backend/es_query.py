import numpy as np
if not hasattr(np, 'float_'):
    np.float_ = np.float64

from elasticsearch import Elasticsearch, helpers

from app.config import settings

# Connect to Elasticsearch using settings
es = Elasticsearch(settings.ES_HOST, verify_certs=False)

INDEX_NAME = settings.ES_INDEX


# res = es.search(index="products", body={"query": {"match_all": {}}, "size": 5})
# for hit in res["hits"]["hits"]:
#     print(hit["_source"])

# Define a sample mapping for the product index (run once)
def create_index():
    if not es.indices.exists(index=INDEX_NAME):
        es.indices.create(
            index=INDEX_NAME,
            body={
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0
                },
                "mappings": {
                    "properties": {
                        "name": {"type": "text"},
                        "description": {"type": "text"},
                        "category": {"type": "keyword"},
                        "color": {"type": "keyword"},
                        "brand": {"type": "keyword"},
                        "gender": {"type": "keyword"},
                        "price": {"type": "integer"},
                        "rating": {"type": "float"},
                        "stock": {"type": "integer"},
                        "discount": {"type": "integer"}
                    }
                }
            }
        )

# Search function
def search_products(category=None, color=None, brand=None, gender=None, price_filter=None, query_text=None):
    must_clauses = []

    if category:
        must_clauses.append({"term": {"category": category.lower()}})
    if color:
        must_clauses.append({"term": {"color": color.lower()}})
    if brand:
        must_clauses.append({"term": {"brand": brand.lower()}})
    if gender:
        must_clauses.append({"term": {"gender": gender.lower()}})
    if price_filter:
        op = price_filter.get("operator")
        if op == "between":
            must_clauses.append({"range": {"price": {"gte": price_filter["min"], "lte": price_filter["max"]}}})
        elif op == ">":
            must_clauses.append({"range": {"price": {"gt": price_filter["value"]}}})
        elif op == "<":
            must_clauses.append({"range": {"price": {"lt": price_filter["value"]}}})
        elif op == ">=":
            must_clauses.append({"range": {"price": {"gte": price_filter["value"]}}})
        elif op == "<=":
            must_clauses.append({"range": {"price": {"lte": price_filter["value"]}}})

    should_clause = []
    if query_text:
        should_clause.append({
            "multi_match": {
                "query": query_text,
                "fields": ["name^3", "description", "category"]
            }
        })

    query_body = {
        "query": {
            "bool": {
                "must": must_clauses,
                "should": should_clause,
                "minimum_should_match": 0
            }
        },
        "sort": [
            {"_score": "desc"},
            {"rating": "desc"},
            {"discount": "desc"},
            {"price": "asc"}
        ]
    }
    
    # Sort now enabled. If this fails, the index must be re-created with correct mapping.
    # query_body["sort"] = [...] 

    
    # es.indices.refresh(index=INDEX_NAME)
    res = es.search(index=INDEX_NAME, body=query_body)
    return [hit["_source"] for hit in res["hits"]["hits"]]

# For standalone testing (optional)
if __name__ == "__main__":

    # if not es.indices.exists(index=INDEX_NAME):
    #     create_index()

    query_data = {'keywords': [], 'category': 'shirts', 'brand': None, 'color': None, 'gender': 'men', 'price_min': None, 'price_max': 3000}
    print(f"Testing Query: {query_data}")


    # Convert query_parser output to search_products args
    p_filter = None
    if query_data['price_min'] is not None and query_data['price_max'] is not None:
        p_filter = {"operator": "between", "min": query_data['price_min'], "max": query_data['price_max']}
    elif query_data['price_max'] is not None:
        p_filter = {"operator": "<=", "value": query_data['price_max']}
    elif query_data['price_min'] is not None:
        p_filter = {"operator": ">=", "value": query_data['price_min']}

    results = search_products(
        category=query_data.get('category'),
        brand=query_data.get('brand'),
        color=query_data.get('color'),
        gender=query_data.get('gender'),
        price_filter=p_filter,
        query_text=" ".join(query_data.get('keywords', []))
    )
    
    print(f"Found {len(results)} results:")
    for r in results:
        print(r)
