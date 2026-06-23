import requests

# Fallback dictionary for common e-commerce terms
# Datamuse can return weird synonyms (slang, etc.), so we have curated product synonyms
PRODUCT_SYNONYMS = {
    "shoes": ["footwear", "sneakers", "trainers", "kicks", "boots"],
    "phone": ["mobile", "smartphone", "cellphone", "handset"],
    "shirt": ["top", "tee", "blouse", "jersey"],
    "pants": ["trousers", "jeans", "slacks"],
    "watch": ["timepiece", "wristwatch", "smartwatch"],
    "bag": ["backpack", "purse", "handbag", "tote"],
    "mug": ["cup", "coffee cup", "tumbler"],
    "laptop": ["notebook", "computer", "pc"],
    "headphones": ["earphones", "earbuds", "headset"],
    "camera": ["dslr", "mirrorless", "camcorder"],
}

def fetch_auto_synonyms(word: str, max_results=10) -> list:
    """
    Fetches synonyms - first from curated dictionary, then from Datamuse API.
    """
    if not word:
        return []
    
    word_lower = word.lower()
    
    # 1. Check curated dictionary first
    if word_lower in PRODUCT_SYNONYMS:
        return PRODUCT_SYNONYMS[word_lower]
    
    # 2. Try Datamuse API with "means like" query for better product relevance
    try:
        url = f"https://api.datamuse.com/words?ml={word}&max={max_results}"
        res = requests.get(url, timeout=2)
        if res.status_code == 200:
            data = res.json()
            # Filter: only single words, lowercase
            synonyms = [item["word"].lower() for item in data if " " not in item["word"]][:max_results]
            if synonyms:
                return synonyms
    except Exception as e:
        print(f"Warning: Failed to fetch auto-synonyms for '{word}': {e}")
    
    return []

if __name__ == "__main__":
    print("Testing auto-synonyms for 'phone':", fetch_auto_synonyms("phone"))
    print("Testing auto-synonyms for 'mug':", fetch_auto_synonyms("mug"))
    print("Testing auto-synonyms for 'sneakers':", fetch_auto_synonyms("sneakers"))
