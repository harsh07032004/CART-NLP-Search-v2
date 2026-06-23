import { clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs) {
  return twMerge(clsx(inputs))
}

export function formatPrice(price) {
  return new Intl.NumberFormat('en-IN', { 
    style: 'currency', 
    currency: 'INR', 
    maximumFractionDigits: 0 
  }).format(price || 0);
}

export function getAvgRating(product) {
  const ratings = product?.userRatings || [];
  if (ratings.length > 0) {
    return ratings.reduce((sum, r) => sum + (r.rating || 0), 0) / ratings.length;
  }
  return product?.rating || 0;
} 