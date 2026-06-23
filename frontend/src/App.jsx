import React, { Suspense, lazy } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";

import { ProductsProvider } from "@/contexts/ProductsContext";
import { CartProvider } from "@/contexts/CartContext";
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { useKeepAlive } from "@/hooks/useKeepAlive";
import { useProducts } from "@/contexts/ProductsContext";

// Eagerly load the two most common pages
import Index from "./pages/Index";
import Products from "./pages/Products";

// Lazy-load heavy/rarely visited pages
const AddProduct    = lazy(() => import("./pages/AddProduct"));
const Cart          = lazy(() => import("./pages/Cart"));
const NotFound      = lazy(() => import("./pages/NotFound"));
const ProductDetail = lazy(() => import("./pages/ProductDetail"));

/** Minimal skeleton shown while a lazy page chunk is loading */
const PageSkeleton = () => (
  <div className="min-h-screen bg-background flex items-center justify-center">
    <div className="flex flex-col items-center gap-4">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary" />
      <p className="text-sm text-muted-foreground">Loading…</p>
    </div>
  </div>
);

/** Inner component that uses ProductsContext (must be inside provider) */
const AppRoutes = () => {
  const { fetchProducts } = useProducts();
  // Keep backend alive — shows "Waking up server…" toast when Render spins down
  useKeepAlive(fetchProducts);

  return (
    <BrowserRouter>
      <Suspense fallback={<PageSkeleton />}>
        <Routes>
          <Route path="/"            element={<Index />} />
          <Route path="/products"    element={<Products />} />
          <Route path="/product/:id" element={<ProductDetail />} />
          <Route path="/add-product" element={<AddProduct />} />
          <Route path="/cart"        element={<Cart />} />
          <Route path="*"            element={<NotFound />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
};

const App = () => (
  <ProductsProvider>
    <CartProvider>
      <TooltipProvider>
        <Toaster />
        <Sonner richColors closeButton />
        <AppRoutes />
      </TooltipProvider>
    </CartProvider>
  </ProductsProvider>
);

export default App;