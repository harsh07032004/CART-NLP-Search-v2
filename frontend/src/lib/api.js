const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";
const TIMEOUT_MS = 10000; // 10 s request timeout

// ---------------------------------------------------------------------------
// Fetch wrapper with timeout
// ---------------------------------------------------------------------------
async function fetchWithTimeout(url, options = {}, timeoutMs = TIMEOUT_MS) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(url, { ...options, signal: controller.signal });
    return res;
  } finally {
    clearTimeout(timer);
  }
}

// ---------------------------------------------------------------------------
// Response → frontend shape normaliser
// ---------------------------------------------------------------------------
const mapToFrontend = (p) => ({
  id: p.id,
  name: p.name,
  description: p.description,
  price: p.price,
  company: p.brand || "Unknown",   // brand → company (legacy frontend key)
  category: p.category,
  image: p.image_url || "https://placehold.co/400x400?text=No+Image",
  userRatings: p.userRatings || [],
  rating: p.rating || 0,
  discount: p.discount || 0,
  stock: p.stock ?? 100,
  isNew: p.isNew || false,
  isSale: p.isSale || false,
  gender: p.gender || "unisex",
  color: p.color || null,
  synonyms: p.synonyms || [],
});

// ---------------------------------------------------------------------------
// API object
// ---------------------------------------------------------------------------
export const api = {
  /** Health probe — used by useKeepAlive to detect backend availability */
  async health() {
    const res = await fetchWithTimeout(`${API_BASE}/health`, {}, 8000);
    if (!res.ok) throw new Error("Health check failed");
    return res.json();
  },

  /** NLP readiness — useful for debugging */
  async nlpStatus() {
    const res = await fetchWithTimeout(`${API_BASE}/nlp-status`);
    if (!res.ok) throw new Error("NLP status failed");
    return res.json();
  },

  /** Full-text + NLP product search */
  async search(query, size = 100) {
    const res = await fetchWithTimeout(
      `${API_BASE}/search?q=${encodeURIComponent(query)}&size=${size}`
    );
    if (!res.ok) throw new Error("Search failed");
    const data = await res.json();
    return data.map(mapToFrontend);
  },

  /**
   * NLP search that also returns parsed metadata (entity chips, did_you_mean, sort_by).
   * Used by SmartSearchBar to render real "AI understood" chips.
   */
  async searchWithMeta(query, size = 100) {
    const res = await fetchWithTimeout(
      `${API_BASE}/search/meta?q=${encodeURIComponent(query)}&size=${size}`
    );
    if (!res.ok) throw new Error("Search failed");
    const data = await res.json();
    return {
      results: (data.results || []).map(mapToFrontend),
      parsed: data.parsed || {},
      did_you_mean: data.did_you_mean || null,
      total: data.total || 0,
    };
  },

  /**
   * Parse a query without running the search — returns entity chips only.
   * Called as the user types (debounced) to show real-time "AI understood" chips.
   */
  async parseQuery(query) {
    const res = await fetchWithTimeout(
      `${API_BASE}/search/parse?q=${encodeURIComponent(query)}`,
      {},
      5000
    );
    if (!res.ok) throw new Error("Parse failed");
    return res.json(); // { query, parsed }
  },

  /**
   * Autocomplete suggestions — called on every keystroke (debounced ~150ms).
   * Returns { suggestions: [{text, type}], products: [{id, name, brand, ...}] }
   */
  async autocomplete(prefix, limit = 6) {
    if (!prefix || prefix.trim().length < 1) return { suggestions: [], products: [] };
    try {
      const res = await fetchWithTimeout(
        `${API_BASE}/search/autocomplete?q=${encodeURIComponent(prefix)}&limit=${limit}`,
        {},
        4000
      );
      if (!res.ok) return { suggestions: [], products: [] };
      return res.json();
    } catch {
      return { suggestions: [], products: [] };
    }
  },

  /** Fetch all products (cached 5 min on backend) */
  async getAll(limit = 200) {
    const res = await fetchWithTimeout(`${API_BASE}/products?limit=${limit}`);
    if (!res.ok) throw new Error("Fetch failed");
    const data = await res.json();
    return data.map(mapToFrontend);
  },

  /** Get single product by ID */
  async getOne(id) {
    const res = await fetchWithTimeout(`${API_BASE}/products/${id}`);
    if (!res.ok) throw new Error("Product not found");
    return mapToFrontend(await res.json());
  },

  /** Create a product */
  async create(product) {
    const payload = {
      name: product.name,
      description: product.description,
      brand: product.company,
      category: product.category,
      price: parseFloat(product.price),
      image_url: product.image,
      gender: product.gender,
      color: product.color,
      rating: parseFloat(product.rating || 0),
      stock: parseInt(product.stock || 100),
      discount: parseInt(product.discount || 0),
    };
    const res = await fetchWithTimeout(`${API_BASE}/products`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Create failed");
    }
    return mapToFrontend(await res.json());
  },

  /** Update an existing product */
  async update(id, updates) {
    const payload = {
      ...(updates.name && { name: updates.name }),
      ...(updates.description && { description: updates.description }),
      ...(updates.company && { brand: updates.company }),
      ...(updates.category && { category: updates.category }),
      ...(updates.price && { price: parseFloat(updates.price) }),
      ...(updates.image && { image_url: updates.image }),
      ...(updates.gender && { gender: updates.gender }),
      ...(updates.color && { color: updates.color }),
      ...(updates.rating !== undefined && { rating: parseFloat(updates.rating) }),
      ...(updates.stock !== undefined && { stock: parseInt(updates.stock) }),
      ...(updates.discount !== undefined && { discount: parseInt(updates.discount) }),
      ...(updates.userRatings !== undefined && { userRatings: updates.userRatings }),
    };
    const res = await fetchWithTimeout(`${API_BASE}/products/${id}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Update failed");
    }
    return mapToFrontend(await res.json());
  },

  /** Delete a product */
  async delete(id) {
    const res = await fetchWithTimeout(`${API_BASE}/products/${id}`, {
      method: "DELETE",
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Delete failed");
    }
    return res.json();
  },

  /** Get similar products */
  async getSimilar(id, limit = 6) {
    const res = await fetchWithTimeout(
      `${API_BASE}/recommendations/similar/${id}?limit=${limit}`
    );
    if (!res.ok) return { similar_products: [] };
    const data = await res.json();
    return { ...data, similar_products: (data.similar_products || []).map(mapToFrontend) };
  },

  /** Get trending products */
  async getTrending(limit = 10) {
    const res = await fetchWithTimeout(
      `${API_BASE}/recommendations/trending?limit=${limit}`
    );
    if (!res.ok) return { trending_products: [] };
    const data = await res.json();
    return { ...data, trending_products: (data.trending_products || []).map(mapToFrontend) };
  },

  /** Analytics stats */
  async getAnalyticsStats(days = 7) {
    const res = await fetchWithTimeout(`${API_BASE}/analytics/stats?days=${days}`);
    if (!res.ok) throw new Error("Stats fetch failed");
    return res.json();
  },

  /** Top searches */
  async getTopSearches(days = 7, limit = 20) {
    const res = await fetchWithTimeout(
      `${API_BASE}/analytics/top-searches?days=${days}&limit=${limit}`
    );
    if (!res.ok) throw new Error("Top searches fetch failed");
    return res.json();
  },

  /** Log a product click for CTR analytics */
  async logClick(query, productId, position = 0) {
    try {
      await fetchWithTimeout(
        `${API_BASE}/analytics/click?query=${encodeURIComponent(query)}&product_id=${productId}&position=${position}`,
        { method: "POST" }
      );
    } catch {
      // Non-critical — swallow silently
    }
  },
};
