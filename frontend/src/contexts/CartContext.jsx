import React, { createContext, useContext, useState } from 'react';

const CartContext = createContext(undefined);

export const useCart = () => {
  const context = useContext(CartContext);
  if (!context) {
    throw new Error('useCart must be used within a CartProvider');
  }
  return context;
};

export const CartProvider = ({ children }) => {
  const [cartItems, setCartItems] = useState([]);
  const [wishlistItems, setWishlistItems] = useState([]);

  const addToCart = async (product) => {
    const existingItem = cartItems.find(item => item.id === product.id);
    if (existingItem) {
      // Update quantity
      setCartItems(prev => prev.map(item => 
        item.id === product.id 
          ? { ...item, quantity: item.quantity + 1 }
          : item
      ));
    } else {
      // Add new item
      setCartItems(prev => [...prev, { ...product, quantity: 1, addedAt: new Date() }]);
    }
  };

  const removeFromCart = async (productId) => {
    setCartItems(prev => prev.filter(item => item.id !== productId));
  };

  const decreaseQuantity = (productId) => {
    setCartItems(prev => prev.map(item => {
      if (item.id === productId) {
        if (item.quantity > 1) {
          return { ...item, quantity: item.quantity - 1 };
        }
        // If quantity would be 0, remove the item
        return null;
      }
      return item;
    }).filter(Boolean));
  };

  const updateQuantity = (productId, newQuantity) => {
    if (newQuantity <= 0) {
      removeFromCart(productId);
      return;
    }
    setCartItems(prev => prev.map(item => 
      item.id === productId 
        ? { ...item, quantity: newQuantity }
        : item
    ));
  };

  const clearCart = () => {
    setCartItems([]);
  };

  const addToWishlist = async (product) => {
    const existing = wishlistItems.find(item => item.id === product.id);
    if (!existing) {
      setWishlistItems(prev => [...prev, { ...product, addedAt: new Date() }]);
    }
  };

  const removeFromWishlist = async (productId) => {
    setWishlistItems(prev => prev.filter(item => item.id !== productId));
  };

  const isInCart = (productId) => {
    return cartItems.some(item => item.id === productId);
  };

  const isInWishlist = (productId) => {
    return wishlistItems.some(item => item.id === productId);
  };

  const getCartCount = () => {
    return cartItems.reduce((total, item) => total + item.quantity, 0);
  };

  return (
    <CartContext.Provider value={{
      cartItems,
      wishlistItems,
      addToCart,
      removeFromCart,
      decreaseQuantity,
      updateQuantity,
      clearCart,
      addToWishlist,
      removeFromWishlist,
      isInCart,
      isInWishlist,
      getCartCount
    }}>
      {children}
    </CartContext.Provider>
  );
}; 