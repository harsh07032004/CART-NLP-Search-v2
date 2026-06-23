import { Star, ShoppingCart, TrendingUp } from "lucide-react";
import { Link } from "react-router-dom";

import { formatPrice, getAvgRating } from "@/lib/utils";

export function ProductCard({ product, onAddToCart }) {
  if (!product) return null;

  const { id, name, price, originalPrice, discount, brand, category, image, userRatings = [] } = product;
  const rating = getAvgRating(product);

  return (
    <div className="bg-white rounded-2xl p-4 shadow-sm hover:shadow-xl transition-all duration-300 border border-gray-100 group relative flex flex-col h-full hover:-translate-y-1">
      {/* Badges */}
      <div className="absolute top-4 inset-x-4 flex justify-between items-start z-10 pointer-events-none">
        <div className="flex flex-col gap-1 items-start">
          {product.isNew && (
            <span className="bg-green-500 text-white text-[10px] font-bold px-2 py-1 rounded-full uppercase tracking-wider shadow-sm">
              NEW
            </span>
          )}
          {product.isSale && (
            <span className="bg-red-500 text-white text-[10px] font-bold px-2 py-1 rounded-full uppercase tracking-wider shadow-sm">
              SALE
            </span>
          )}
          {discount >= 20 && !product.isSale && (
            <span className="bg-red-500 text-white text-[10px] font-bold px-2 py-1 rounded-full uppercase tracking-wider shadow-sm">
              {discount}% OFF
            </span>
          )}
        </div>
        {rating >= 4.5 && (
          <span className="bg-amber-100 text-amber-700 text-[10px] font-bold px-2 py-1 rounded-full flex items-center gap-1 shadow-sm border border-amber-200">
            <TrendingUp className="h-3 w-3" /> TOP
          </span>
        )}
      </div>

      {/* Image */}
      <Link to={`/product/${id}`} className="relative h-48 w-full rounded-xl bg-gray-50 mb-4 overflow-hidden block">
        <img src={image} alt={name} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" loading="lazy" />
      </Link>

      {/* Content */}
      <div className="flex flex-col flex-1">
        <div className="flex items-center gap-2 mb-2 text-xs font-medium text-gray-500">
          <span className="capitalize">{brand}</span>
          <span className="w-1 h-1 rounded-full bg-gray-300" />
          <span className="capitalize">{category}</span>
        </div>

        <Link to={`/product/${id}`}>
          <h3 className="font-bold text-gray-900 leading-snug line-clamp-2 hover:text-blue-600 transition-colors">
            {name}
          </h3>
        </Link>

        {/* Rating */}
        <div className="flex items-center gap-1 mt-2 mb-4">
          <Star className={`h-4 w-4 ${rating > 0 ? "fill-amber-400 text-amber-400" : "text-gray-300"}`} />
          <span className="text-sm font-bold text-gray-900">{rating > 0 ? rating.toFixed(1) : "New"}</span>
          <span className="text-xs text-gray-500">({userRatings.length})</span>
        </div>

        {/* Bottom row */}
        <div className="mt-auto flex items-end justify-between">
          <div>
            {discount > 0 && (
              <p className="text-xs text-gray-400 line-through mb-0.5">{formatPrice(originalPrice)}</p>
            )}
            <p className="text-lg font-black text-blue-600 leading-none">{formatPrice(price)}</p>
          </div>

          <button 
            onClick={(e) => { e.preventDefault(); onAddToCart(product); }}
            className="flex items-center justify-center h-10 w-10 rounded-full bg-gray-100 text-gray-700 hover:bg-blue-600 hover:text-white transition-colors"
            title="Add to Cart"
          >
            <ShoppingCart className="h-5 w-5" />
          </button>
        </div>
      </div>
    </div>
  );
}