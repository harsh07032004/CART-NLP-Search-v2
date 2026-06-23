
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { Header } from "@/components/Header";
import { useCart } from "@/contexts/CartContext";
import { useProducts } from "@/contexts/ProductsContext";
import { UserRating } from "@/components/UserRating";
import { Trash2, Minus, Plus, ShoppingBag, ArrowRight, Package, Shield, Zap } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { formatPrice } from "@/lib/utils";

const PERKS = [
  { icon: Package, label: "Free Delivery", sub: "On all orders" },
  { icon: Shield, label: "Secure Payment", sub: "SSL encrypted" },
  { icon: Zap, label: "Fast Dispatch", sub: "Within 24 hrs" },
];

export default function Cart() {
  const { cartItems, removeFromCart, addToCart, decreaseQuantity, getCartCount, clearCart } = useCart();
  const { rateProduct } = useProducts();
  const navigate = useNavigate();
  const { toast } = useToast();

  const handleCheckout = () => {
    toast({
      title: "Purchased successfully 🎉",
      description: "Thank you for your order!",
    });
    clearCart();
  };

  const handleQuantityChange = (productId, change) => {
    if (change > 0) {
      const item = cartItems.find(i => i.id === productId);
      if (item) addToCart(item);
    } else {
      decreaseQuantity(productId);
    }
  };

  const totalAmount = cartItems.reduce((total, item) => total + item.price * item.quantity, 0);
  const tax = totalAmount * 0.1;
  const grand = totalAmount + tax;

  return (
    <div className="page-wrapper min-h-screen bg-background">
      <Header onSearch={() => {}} cartCount={getCartCount()} />

      <main className="page-content container mx-auto max-w-6xl px-4 py-10">
        {/* Page title */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="mb-8">
          <p className="section-eyebrow mb-2">Review Items</p>
          <div className="flex items-baseline gap-3">
            <h1 className="text-3xl font-bold" style={{ fontFamily: "'Plus Jakarta Sans', sans-serif", letterSpacing: "-0.025em" }}>Shopping Cart</h1>
            {cartItems.length > 0 && (
              <span className="badge badge-blue">
                {cartItems.length} {cartItems.length === 1 ? "item" : "items"}
              </span>
            )}
          </div>
        </motion.div>

        {/* Empty State */}
        {cartItems.length === 0 ? (
          <motion.div initial={{ opacity: 0, scale: 0.94 }} animate={{ opacity: 1, scale: 1 }} className="flex flex-col items-center justify-center py-24 text-center">
            <div className="w-24 h-24 rounded-3xl bg-blue-50 border border-blue-100 flex items-center justify-center mb-6">
              <ShoppingBag className="h-12 w-12 text-blue-600" />
            </div>
            <h2 className="text-2xl font-bold mb-2" style={{ fontFamily: "'Plus Jakarta Sans', sans-serif", letterSpacing: "-0.025em" }}>Your cart is empty</h2>
            <p className="text-gray-500 mb-8 max-w-sm">Looks like you haven't added anything yet. Explore our collection!</p>
            <button onClick={() => navigate("/products")} className="btn-primary gap-2">
              <ShoppingBag className="h-4 w-4" />
              Start Shopping
              <ArrowRight className="h-4 w-4" />
            </button>
          </motion.div>
        ) : (
          <div className="grid lg:grid-cols-3 gap-6">
            {/* ── Cart Items ── */}
            <div className="lg:col-span-2 space-y-4">
              <AnimatePresence>
                {cartItems.map((item, idx) => (
                  <motion.div key={item.id} layout initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, x: -40, scale: 0.95 }} transition={{ duration: 0.3, delay: idx * 0.04 }} className="surface-1 p-4 sm:p-5">
                    <div className="flex gap-4">
                      {/* Image */}
                      <div className="relative flex-shrink-0">
                        <div className="w-24 h-24 sm:w-28 sm:h-28 rounded-xl overflow-hidden bg-slate-100">
                          <img
                            src={item.image}
                            alt={item.name}
                            className="w-full h-full object-cover"
                          />
                        </div>
                      </div>

                      {/* Details */}
                      <div className="flex-1 min-w-0 space-y-2">
                        <div className="flex items-start justify-between gap-2">
                          <div>
                            <p className="text-xs font-bold uppercase tracking-wider text-blue-500">{item.company}</p>
                            <h3 className="font-semibold text-sm sm:text-base text-gray-900 leading-snug">{item.name}</h3>
                            <p className="text-xs text-gray-500 mt-0.5 capitalize">{item.category}</p>
                          </div>
                          <button
                            onClick={() => removeFromCart(item.id)}
                            className="flex-shrink-0 h-8 w-8 rounded-xl flex items-center justify-center text-gray-400 hover:text-red-500 hover:bg-red-50 transition-all"
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </button>
                        </div>

                        <div className="flex items-center justify-between">
                          {/* Qty controls */}
                          <div className="flex items-center gap-0.5 bg-gray-50 rounded-xl p-0.5">
                            <button
                              onClick={() => handleQuantityChange(item.id, -1)}
                              className="h-7 w-7 rounded-lg flex items-center justify-center text-gray-600 hover:bg-white transition-colors"
                            >
                              <Minus className="h-3 w-3" />
                            </button>
                            <span className="w-8 text-center text-sm font-bold text-gray-900">{item.quantity}</span>
                            <button
                              onClick={() => handleQuantityChange(item.id, 1)}
                              className="h-7 w-7 rounded-lg flex items-center justify-center text-gray-600 hover:bg-white transition-colors"
                            >
                              <Plus className="h-3 w-3" />
                            </button>
                          </div>

                          {/* Price */}
                          <div className="text-right">
                            <p className="font-bold text-base text-gray-900">{formatPrice(item.price * item.quantity)}</p>
                            <p className="text-xs text-gray-400">{formatPrice(item.price)} each</p>
                          </div>
                        </div>

                        {/* Rating */}
                        <div className="pt-2 border-t border-gray-100">
                          <UserRating productId={item.id} userRatings={item.userRatings} onRate={rateProduct} />
                        </div>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>

            {/* ── Order Summary ── */}
            <div className="lg:col-span-1">
              <div className="surface-1 p-5 sticky top-24 space-y-5">
                <h2 className="font-bold text-lg" style={{ fontFamily: "'Plus Jakarta Sans', sans-serif" }}>Order Summary</h2>

                <div className="space-y-2.5 text-sm">
                  {[
                    { label: "Subtotal", value: formatPrice(totalAmount) },
                    { label: "Shipping", value: "Free", valueClass: "text-blue-600 font-semibold" },
                    { label: "Tax (10%)", value: formatPrice(tax) },
                  ].map(row => (
                    <div key={row.label} className="flex justify-between">
                      <span className="text-gray-500">{row.label}</span>
                      <span className={row.valueClass || "text-gray-900 font-medium"}>{row.value}</span>
                    </div>
                  ))}
                  <div className="pt-2 border-t border-gray-200 flex justify-between font-bold text-base">
                    <span className="text-gray-900">Total</span>
                    <span className="text-gradient-blue text-lg">{formatPrice(grand)}</span>
                  </div>
                </div>

                <button onClick={handleCheckout} className="btn-primary w-full rounded-full gap-2">
                  Proceed to Checkout <ArrowRight className="h-4 w-4" />
                </button>

                <button onClick={() => navigate("/products")} className="w-full py-2.5 text-sm font-medium text-muted-foreground hover:text-foreground transition-colors">← Continue Shopping</button>

                <div className="pt-3 border-t border-gray-100 grid grid-cols-3 gap-2">
                  {PERKS.map(({ icon: Icon, label, sub }) => (
                    <div key={label} className="flex flex-col items-center text-center gap-1">
                      <div className="w-8 h-8 rounded-xl bg-blue-50 flex items-center justify-center">
                        <Icon className="h-3.5 w-3.5 text-blue-600" />
                      </div>
                      <p className="text-[10px] font-bold text-gray-700">{label}</p>
                      <p className="text-[9px] text-gray-500">{sub}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}