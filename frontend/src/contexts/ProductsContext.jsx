import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { api } from '@/lib/api';
import { toast } from 'sonner';

const ProductsContext = createContext(undefined);

export const useProducts = () => {
  const context = useContext(ProductsContext);
  if (!context) throw new Error('useProducts must be used within a ProductsProvider');
  return context;
};

export const ProductsProvider = ({ children }) => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isSearching, setIsSearching] = useState(false);
  const [lastQuery, setLastQuery] = useState('');

  const fetchProducts = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.getAll();
      setProducts(data);
    } catch (error) {
      console.error('Failed to fetch products', error);
      toast.error('Failed to load products. Please try again.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchProducts();
  }, [fetchProducts]);

  const searchProducts = useCallback(async (query) => {
    if (!query || !query.trim()) {
      setLastQuery('');
      return fetchProducts();
    }
    setLastQuery(query.trim());
    setIsSearching(true);
    try {
      const data = await api.search(query.trim());
      setProducts(data);
    } catch (error) {
      console.error('Search failed', error);
      toast.error('Search failed. Please try again.');
    } finally {
      setIsSearching(false);
    }
  }, [fetchProducts]);

  const addProduct = useCallback(async (productData) => {
    try {
      const newProduct = await api.create(productData);
      setProducts(prev => [newProduct, ...prev]);
      toast.success(`"${newProduct.name}" added successfully!`);
      return newProduct;
    } catch (error) {
      console.error('Failed to add product', error);
      toast.error(`Failed to add product: ${error.message}`);
      throw error;
    }
  }, []);

  const updateProduct = useCallback(async (id, productData) => {
    try {
      const updated = await api.update(id, productData);
      setProducts(prev => prev.map(p => p.id === id ? updated : p));
      toast.success('Product updated successfully!');
      return updated;
    } catch (error) {
      console.error('Failed to update product', error);
      toast.error(`Failed to update: ${error.message}`);
      throw error;
    }
  }, []);

  const deleteProduct = useCallback(async (id) => {
    // Optimistic removal
    setProducts(prev => prev.filter(p => p.id !== id));
    try {
      await api.delete(id);
      toast.success('Product deleted.');
    } catch (error) {
      console.error('Failed to delete product', error);
      toast.error(`Delete failed: ${error.message}`);
      // Re-fetch to restore correct state
      fetchProducts();
    }
  }, [fetchProducts]);

  const rateProduct = useCallback(async (productId, rating) => {
    const newRating = { userId: `user${Date.now()}`, rating, timestamp: new Date() };
    
    let targetProduct = products.find(p => p.id === productId);
    if (!targetProduct) {
      try {
        targetProduct = await api.getOne(productId);
      } catch (error) {
        console.error('Failed to find product to rate', error);
        return null;
      }
    }
    
    const updatedRatings = [...(targetProduct.userRatings || []), newRating];
    const avg = updatedRatings.reduce((s, r) => s + r.rating, 0) / updatedRatings.length;
    const newRatingAvg = Math.round(avg * 10) / 10;
    
    // Optimistic local update
    setProducts(prev => prev.map(p => p.id === productId ? { ...p, userRatings: updatedRatings, rating: newRatingAvg } : p));
    
    try {
      const updated = await api.update(productId, { userRatings: updatedRatings, rating: newRatingAvg });
      return updated;
    } catch (error) {
      console.error('Failed to save rating', error);
      toast.error('Failed to save your rating.');
      fetchProducts(); // Revert on failure
      return null;
    }
  }, [products, fetchProducts]);

  return (
    <ProductsContext.Provider value={{
      products,
      loading,
      isSearching,
      lastQuery,
      addProduct,
      updateProduct,
      deleteProduct,
      rateProduct,
      searchProducts,
      fetchProducts,
    }}>
      {children}
    </ProductsContext.Provider>
  );
};