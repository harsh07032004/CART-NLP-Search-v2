import { useState } from "react";
import { motion } from "framer-motion";
import { X, SlidersHorizontal, Star, RotateCcw } from "lucide-react";
import { Slider } from "@/components/ui/slider";
import { formatPrice } from "@/lib/utils";

const CATEGORIES = [
  { id: "shoes",    emoji: "👟", label: "Shoes" },
  { id: "phone",    emoji: "📱", label: "Phones" },
  { id: "earphone", emoji: "🎧", label: "Earphones" },
  { id: "shirts",   emoji: "👕", label: "Shirts" },
  { id: "watches",  emoji: "⌚", label: "Watches" },
  { id: "laptop",   emoji: "💻", label: "Laptops" },
  { id: "jeans",    emoji: "👖", label: "Jeans" },
  { id: "bags",     emoji: "👜", label: "Bags" },
  { id: "jackets",  emoji: "🧥", label: "Jackets" },
];

export function FilterPanel({ onFilterChange, isVisible, onToggle }) {
  const [filters, setFilters] = useState({
    categories: [],
    priceRange: [0, 200000],
    rating: 0,
  });

  const updateFilters = (newFilters) => {
    const updated = { ...filters, ...newFilters };
    setFilters(updated);
    onFilterChange(updated);
  };

  const toggleCategory = (id) => {
    const updated = filters.categories.includes(id)
      ? filters.categories.filter(c => c !== id)
      : [...filters.categories, id];
    updateFilters({ categories: updated });
  };

  const clearFilters = () => {
    const cleared = { categories: [], priceRange: [0, 200000], rating: 0 };
    setFilters(cleared);
    onFilterChange(cleared);
  };

  if (!isVisible) return null;

  const activeCount =
    filters.categories.length +
    (filters.rating > 0 ? 1 : 0) +
    (filters.priceRange[0] > 0 || filters.priceRange[1] < 200000 ? 1 : 0);

  return (
    <div className="filter-sidebar p-5 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-lg bg-blue-50 flex items-center justify-center">
            <SlidersHorizontal className="h-3.5 w-3.5 text-blue-500" />
          </div>
          <h3 className="font-bold text-sm text-gray-900" style={{ fontFamily: "'Plus Jakarta Sans', sans-serif" }}>Filters</h3>
          {activeCount > 0 && (
            <span className="px-1.5 py-0.5 rounded-full bg-blue-50 text-blue-600 text-[10px] font-bold border border-blue-200">
              {activeCount}
            </span>
          )}
        </div>
        <div className="flex items-center gap-1">
          {activeCount > 0 && (
            <button
              onClick={clearFilters}
              className="flex items-center gap-1 px-2 py-1 text-[11px] text-gray-500 hover:text-blue-500 transition-colors rounded-lg hover:bg-blue-50"
            >
              <RotateCcw className="h-3 w-3" /> Reset
            </button>
          )}
          <button
            onClick={onToggle}
            className="lg:hidden h-7 w-7 flex items-center justify-center rounded-lg hover:bg-gray-100 text-gray-400 hover:text-gray-700 transition-colors"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>

      {/* Categories */}
      <div className="space-y-2.5">
        <p className="text-[10px] uppercase tracking-widest text-blue-500 font-mono font-bold">Category</p>
        <div className="flex flex-wrap gap-1.5">
          {CATEGORIES.map(cat => {
            const active = filters.categories.includes(cat.id);
            return (
              <motion.button
                key={cat.id}
                onClick={() => toggleCategory(cat.id)}
                whileTap={{ scale: 0.92 }}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold border transition-all duration-200 ${
                  active
                    ? "bg-blue-50 border-blue-200 text-blue-600 shadow-sm"
                    : "bg-gray-50 border-gray-200 text-gray-600 hover:border-blue-300 hover:text-blue-600 hover:bg-blue-50/50"
                }`}
              >
                <span>{cat.emoji}</span>
                {cat.label}
              </motion.button>
            );
          })}
        </div>
      </div>

      {/* Price Range */}
      <div className="space-y-3">
        <p className="text-[10px] uppercase tracking-widest text-blue-500 font-mono font-bold">Price Range</p>
        <Slider
          value={filters.priceRange}
          onValueChange={(value) => updateFilters({ priceRange: value })}
          max={200000}
          min={0}
          step={1000}
          className="w-full"
        />
        <div className="flex justify-between gap-2">
          <span className="text-xs font-mono bg-gray-50 border border-gray-200 rounded-lg px-2.5 py-1.5 text-blue-600 font-semibold">
            {formatPrice(filters.priceRange[0])}
          </span>
          <span className="text-xs text-gray-400 self-center">–</span>
          <span className="text-xs font-mono bg-gray-50 border border-gray-200 rounded-lg px-2.5 py-1.5 text-blue-600 font-semibold">
            {formatPrice(filters.priceRange[1])}
          </span>
        </div>
      </div>

      {/* Rating */}
      <div className="space-y-2.5">
        <p className="text-[10px] uppercase tracking-widest text-blue-500 font-mono font-bold">Min. Rating</p>
        <div className="flex gap-1.5">
          {[1, 2, 3, 4, 5].map(r => (
            <motion.button
              key={r}
              whileTap={{ scale: 0.85 }}
              onClick={() => updateFilters({ rating: filters.rating === r ? 0 : r })}
              className={`flex-1 flex flex-col items-center gap-0.5 py-2 rounded-xl border text-[10px] font-bold transition-all ${
                filters.rating >= r
                  ? "bg-amber-50 border-amber-200 text-amber-600 shadow-sm"
                  : "bg-gray-50 border-gray-200 text-gray-500 hover:border-amber-300"
              }`}
            >
              <Star className={`h-3 w-3 ${filters.rating >= r ? "fill-amber-400 text-amber-400" : "text-gray-400"}`} />
              {r}
            </motion.button>
          ))}
        </div>
        {filters.rating > 0 && (
          <p className="text-[10px] text-gray-400 font-mono">{filters.rating}+ stars</p>
        )}
      </div>

      {/* Clear all */}
      {activeCount > 0 && (
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
          <div className="pt-2 border-t border-gray-100">
            <button
              onClick={clearFilters}
              className="w-full py-2.5 rounded-xl text-xs font-semibold border border-red-200 text-red-500 hover:bg-red-50 transition-colors"
            >
              Clear All Filters
            </button>
          </div>
        </motion.div>
      )}
    </div>
  );
}