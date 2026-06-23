import { useState, useEffect } from "react";
import { SearchX, RotateCcw, SlidersHorizontal } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useSearchParams } from "react-router-dom";
import { Header } from "@/components/Header";
import { ProductCard } from "@/components/ProductCard";
import { FilterPanel } from "@/components/FilterPanel";
import { useToast } from "@/hooks/use-toast";
import { useCart } from "@/contexts/CartContext";
import { useProducts } from "@/contexts/ProductsContext";
import { getAvgRating } from "@/lib/utils";

/** Skeleton card */
const SkeletonCard = () => (
  <div className="rounded-2xl bg-white border border-slate-200 overflow-hidden animate-pulse">
    <div className="h-44 bg-slate-100" />
    <div className="p-4 space-y-3">
      <div className="h-3 bg-slate-200 rounded-full w-1/3" />
      <div className="h-4 bg-slate-200 rounded-full w-3/4" />
      <div className="h-3 bg-slate-200 rounded-full w-1/2" />
      <div className="h-9 bg-slate-200 rounded-xl" />
    </div>
  </div>
);

const SkeletonGrid = ({ count = 8 }) => (
  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
    {Array.from({ length: count }).map((_, i) => (
      <motion.div key={i} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: i * 0.04 }}>
        <SkeletonCard />
      </motion.div>
    ))}
  </div>
);

/** Empty state */
const EmptyState = ({ query, onReset }) => (
  <motion.div
    initial={{ opacity: 0, y: 24 }}
    animate={{ opacity: 1, y: 0 }}
    className="flex flex-col items-center justify-center py-24 text-center"
  >
    <div className="w-20 h-20 rounded-3xl glass flex items-center justify-center mb-6">
      <SearchX className="h-10 w-10 text-blue-400" />
    </div>
    <h3 className="text-xl font-bold text-slate-800 mb-2">No results found</h3>
    <p className="text-slate-500 max-w-sm mb-2">
      Nothing matched <span className="font-semibold text-slate-700">"{query}"</span>
    </p>
    <p className="text-sm text-slate-400 mb-8 max-w-sm">
      Try simpler keywords or check spelling. Our NLP engine understands typos — try{" "}
      <em className="text-blue-500">red shoes under 2000</em>.
    </p>
    <button
      onClick={onReset}
      className="flex items-center gap-2 px-5 py-2.5 rounded-xl border border-slate-200 text-slate-600 hover:bg-slate-50 transition-all font-medium text-sm"
    >
      <RotateCcw className="h-4 w-4" /> Show all products
    </button>
  </motion.div>
);

const Products = () => {
  const { products, searchProducts, fetchProducts, loading, isSearching, lastQuery } = useProducts();
  const { addToCart, getCartCount } = useCart();
  const [searchParams] = useSearchParams();
  const [filteredProducts, setFilteredProducts] = useState(products);
  const [searchQuery, setSearchQuery] = useState("");
  const [isFilterVisible, setIsFilterVisible] = useState(false);
  const [activeFilters, setActiveFilters] = useState(null);
  const { toast } = useToast();

  useEffect(() => {
    if (activeFilters) {
      setFilteredProducts(applyFilters(activeFilters, products));
    } else {
      setFilteredProducts(products);
    }
  }, [products]); // eslint-disable-line

  useEffect(() => {
    const sp = searchParams.get("search");
    if (sp && sp !== searchQuery) {
      setSearchQuery(sp);
      searchProducts(sp);
    }
  }, [searchParams]); // eslint-disable-line

  const applyFilters = (filters, list) => {
    let r = list;
    if (filters.categories?.length > 0) {
      const lc = filters.categories.map(c => c.toLowerCase());
      r = r.filter(p => lc.includes((p.category || "").toLowerCase()));
    }
    if (filters.priceRange?.length === 2) {
      r = r.filter(p => p.price >= filters.priceRange[0] && p.price <= filters.priceRange[1]);
    }
    if (filters.rating > 0) {
      r = r.filter(p => getAvgRating(p) >= filters.rating);
    }
    return r;
  };

  const handleSearch = (q) => {
    setSearchQuery(q);
    setActiveFilters(null);
    searchProducts(q);
  };

  const handleFilterChange = (filters) => {
    setActiveFilters(filters);
    setFilteredProducts(applyFilters(filters, products));
  };

  const handleReset = () => {
    setSearchQuery("");
    setActiveFilters(null);
    fetchProducts();
  };

  const handleAddToCart = (product) => {
    addToCart(product);
    toast({ title: "Added to cart ✓", description: product.name });
  };

  const showSkeleton = loading || isSearching;
  const showEmpty = !showSkeleton && filteredProducts.length === 0 && (searchQuery || lastQuery);

  return (
    <div className="page-wrapper min-h-screen bg-slate-50 hero-bg">
      <Header onSearch={handleSearch} cartCount={getCartCount()} />

      <main className="page-content container mx-auto px-4 py-10">
        {/* ── Page Header ── */}
        <motion.div
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <p className="section-label mb-2">
            {searchQuery ? "Search Results" : "Browse Collection"}
          </p>
          <div className="flex items-start justify-between gap-4 flex-wrap">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 leading-tight" style={{ fontFamily: "'Plus Jakarta Sans', sans-serif", letterSpacing: "-0.025em" }}>
                {searchQuery ? (
                  <>
                    <span className="text-gray-500 font-normal text-2xl">Results for </span>
                    <span className="text-gradient-blue">"{searchQuery}"</span>
                  </>
                ) : (
                  "All Products"
                )}
              </h1>
              {!showSkeleton && !showEmpty && (
                <p className="text-sm text-gray-500 mt-1 font-mono">
                  {filteredProducts.length} products{searchQuery ? " · NLP-ranked" : ""}
                </p>
              )}
            </div>

            {/* Mobile filter toggle */}
            <button
              onClick={() => setIsFilterVisible(!isFilterVisible)}
              className={`lg:hidden flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold border transition-all ${
                isFilterVisible
                  ? "border-blue-500/50 bg-blue-500/10 text-blue-600"
                  : "border-gray-200 text-gray-600 hover:border-blue-300"
              }`}
            >
              <SlidersHorizontal className="h-4 w-4" />
              Filters
              {activeFilters && (
                <span className="w-4 h-4 rounded-full bg-blue-600 text-white text-[9px] font-bold flex items-center justify-center">
                  {(activeFilters.categories?.length || 0) + (activeFilters.rating > 0 ? 1 : 0)}
                </span>
              )}
            </button>
          </div>
        </motion.div>

        <div className="flex flex-col lg:flex-row gap-6">
          {/* ── Filter Sidebar ── */}
          <AnimatePresence>
            {(isFilterVisible || window.innerWidth >= 1024) && (
              <motion.aside
                initial={{ opacity: 0, x: -16 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -16 }}
                transition={{ duration: 0.25 }}
                className={`lg:w-60 flex-shrink-0 ${isFilterVisible ? "block" : "hidden"} lg:block`}
              >
                <div className="sticky top-24">
                  <FilterPanel
                    onFilterChange={handleFilterChange}
                    isVisible={true}
                    onToggle={() => setIsFilterVisible(false)}
                  />
                </div>
              </motion.aside>
            )}
          </AnimatePresence>

          {/* ── Products Area ── */}
          <div className="flex-1 min-w-0">
            {showSkeleton && <SkeletonGrid count={8} />}
            {showEmpty && <EmptyState query={searchQuery || lastQuery} onReset={handleReset} />}
            {!showSkeleton && !showEmpty && (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {filteredProducts.map((product) => (
                  <ProductCard
                    key={product.id}
                    product={product}
                    onAddToCart={handleAddToCart}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default Products;