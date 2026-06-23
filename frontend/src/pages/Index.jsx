import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Zap } from "lucide-react";
import { Header } from "@/components/Header";
import { ProductCard } from "@/components/ProductCard";
import { FilterPanel } from "@/components/FilterPanel";
import { SmartSearchBar } from "@/components/SmartSearchBar";
import { useToast } from "@/hooks/use-toast";
import { useProducts } from "@/contexts/ProductsContext";
import { useCart } from "@/contexts/CartContext";
import { getAvgRating } from "@/lib/utils";

export default function Index() {
  const ctx = useProducts();
  const { products } = ctx;
  const { addToCart, getCartCount } = useCart();
  const [filtered, setFiltered] = useState(products);
  const [query, setQuery] = useState("");
  const { toast } = useToast();

  useEffect(() => setFiltered(products), [products]);

  const onSearch = async (q) => { 
    setQuery(q); 
    await ctx.searchProducts(q); 
  };

  const onFilter = (f) => {
    let r = products;
    if (f.categories.length) r = r.filter(p => f.categories.includes(p.category));
    r = r.filter(p => p.price >= f.priceRange[0] && p.price <= f.priceRange[1]);
    if (f.rating > 0) r = r.filter(p => getAvgRating(p) >= f.rating);
    setFiltered(r);
  };

  const addCart = (p) => { 
    addToCart(p); 
    toast({ title: "Added to cart", description: p.name }); 
  };

  return (
    <div className="min-h-screen overflow-x-hidden bg-gray-50">
      <Header onSearch={onSearch} cartCount={getCartCount()} />

      {/* ══ HERO SECTION (Kept as requested) ══ */}
      <section className="relative min-h-[92vh] flex items-center overflow-hidden pt-24" style={{ background: "linear-gradient(135deg, #dbeafe 0%, #ede9fe 35%, #e0e7ff 65%, #dbeafe 100%)" }}>
        <div className="blob w-[560px] h-[560px] top-[-100px] left-[-80px]" style={{ background: "radial-gradient(circle, rgba(99,102,241,0.30) 0%, rgba(139,92,246,0.18) 40%, transparent 70%)" }} />
        <div className="blob w-[480px] h-[480px] bottom-[-60px] right-[-60px]" style={{ background: "radial-gradient(circle, rgba(59,130,246,0.28) 0%, rgba(99,102,241,0.16) 40%, transparent 70%)" }} />
        <div className="absolute inset-0 pointer-events-none opacity-30" style={{ backgroundImage: "radial-gradient(rgba(99,102,241,0.15) 1px,transparent 1px)", backgroundSize: "28px 28px" }} />

        <div className="relative z-10 section-inner pt-16 pb-32 grid lg:grid-cols-2 gap-16 items-center max-w-7xl mx-auto px-6">
          <div>
            <motion.div initial={{ opacity: 0, y: -12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}
              className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-semibold uppercase tracking-widest mb-8 mt-2"
              style={{ background: "rgba(99,102,241,0.10)", color: "#4F46E5", border: "1px solid rgba(99,102,241,0.20)", backdropFilter: "blur(12px)" }}>
              <span className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse-soft" />
              NLP-Powered Search Engine
            </motion.div>

            <motion.h1 initial={{ opacity: 0, y: 32 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8, delay: 0.1 }}
              className="text-5xl sm:text-6xl lg:text-[64px] font-bold text-gray-900 mb-5 leading-tight tracking-tight">
              Find what <br />
              <span className="text-blue-600">feels right.</span>
            </motion.h1>

            <motion.p initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.22 }}
              className="text-lg text-gray-600 mb-8 max-w-md leading-relaxed">
              Lightning fast search. Exceptionally relevant results.<br />
              <span className="text-sm font-mono text-gray-400 mt-1 block">Try searching "red running shoes"</span>
            </motion.p>

            <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}
              className="bg-white/40 backdrop-blur-md rounded-2xl p-4 mb-6 shadow-sm border border-white/60">
              <SmartSearchBar onSearchSubmit={onSearch} />
            </motion.div>
          </div>
          <motion.div initial={{ opacity: 0, x: 40 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.9, delay: 0.2 }}
            className="hidden lg:flex items-center justify-center relative h-[500px]">
            <div className="absolute w-[360px] h-[360px] rounded-full" style={{ background: "radial-gradient(circle, rgba(29,107,240,0.08) 0%, rgba(100,130,255,0.05) 50%, transparent 70%)" }} />
            <div className="absolute z-20 top-[15%] left-[25%] bg-white/60 backdrop-blur-md p-3 rounded-2xl shadow-xl border border-white/40">
              <img src="https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800&q=80" alt="Headphones" className="w-56 h-56 object-cover rounded-xl" />
              <div className="mt-3 px-1 pb-1">
                <p className="text-xs font-bold text-gray-900">Sony WH-1000XM5</p>
                <p className="text-[11px] text-gray-500">Noise Cancelling Wireless</p>
                <p className="text-sm font-black text-blue-600 mt-2">₹29,990</p>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* ══ SIMPLE PRODUCT GRID ══ */}
      <section className="max-w-7xl mx-auto px-6 py-16">
        <div className="flex items-center justify-between mb-8 pb-5 border-b border-gray-200">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">
              {query ? `Results for "${query}"` : "All Products"}
            </h2>
            <p className="text-sm text-gray-500 mt-1">{filtered.length} products found</p>
          </div>
        </div>

        <div className="flex flex-col lg:flex-row gap-8">
          {/* Static Sidebar Filter */}
          <div className="lg:w-64 flex-shrink-0 hidden lg:block">
            <FilterPanel onFilterChange={onFilter} isVisible={true} onToggle={() => {}} />
          </div>
          
          {/* Main Grid */}
          <div className="flex-1 min-w-0">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {filtered.map((product) => (
                <ProductCard
                  key={product.id}
                  product={product}
                  onAddToCart={addCart}
                />
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ══ SIMPLE FOOTER ══ */}
      <footer className="bg-white border-t border-gray-200 py-8">
        <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row justify-between items-center gap-4 text-sm text-gray-500">
          <div className="flex items-center gap-2">
            <Zap className="h-4 w-4 text-blue-600" />
            <span className="font-bold text-gray-900">Created by Harsh</span>
          </div>
          <p>© 2025</p>
        </div>
      </footer>
    </div>
  );
}