import { useState, useEffect } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import {
  ShoppingCart, Heart, Star, Share2, Tag,
  CheckCircle2, XCircle, Sparkles, ChevronRight,
} from "lucide-react";
import { Header } from "@/components/Header";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useCart } from "@/contexts/CartContext";
import { useProducts } from "@/contexts/ProductsContext";
import { useToast } from "@/hooks/use-toast";
import { api } from "@/lib/api";
import { formatPrice, getAvgRating } from "@/lib/utils";

const Skeleton = ({ className }) => (
  <div className={`animate-pulse bg-muted rounded-lg ${className}`} />
);

const ReviewCard = ({ review, index }) => (
  <div className="border border-border rounded-xl p-4 space-y-2">
    <div className="flex items-center justify-between">
      <span className="font-semibold text-sm">
        {review.user || `User ${index + 1}`}
      </span>
      <div className="flex items-center gap-0.5">
        {Array.from({ length: 5 }).map((_, i) => (
          <Star key={i} className={`h-3.5 w-3.5 ${i < (review.rating || 0) ? "text-amber-400 fill-amber-400" : "text-muted-foreground/30"}`} />
        ))}
      </div>
    </div>
    {review.comment && <p className="text-sm text-muted-foreground">{review.comment}</p>}
  </div>
);

const ProductDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { addToCart, addToWishlist, removeFromWishlist, isInWishlist, getCartCount } = useCart();
  const { products, rateProduct } = useProducts();
  const { toast } = useToast();

  const [product, setProduct] = useState(null);
  const [similar, setSimilar] = useState([]);
  const [loading, setLoading] = useState(true);
  const [qty, setQty] = useState(1);
  const [hoverRating, setHoverRating] = useState(0);
  const [userRating, setUserRating] = useState(0);
  const [activeTab, setActiveTab] = useState("description");

  useEffect(() => {
    const local = products.find((p) => p.id === id);
    if (local) { setProduct(local); setLoading(false); }
    else {
      setLoading(true);
      api.getOne(id).then(setProduct).catch(() => toast({ title: "Product not found", variant: "destructive" })).finally(() => setLoading(false));
    }
  }, [id, products]);

  useEffect(() => {
    api.getSimilar(id, 6).then((d) => setSimilar(d.similar_products || []));
  }, [id]);
  if (loading) return (
    <div className="min-h-screen page-wrapper hero-bg">
      <Header cartCount={getCartCount()} />
      <main className="container mx-auto px-4 py-8">
        <div className="grid lg:grid-cols-2 gap-12">
          <Skeleton className="aspect-square w-full" />
          <div className="space-y-4">{Array.from({length:6}).map((_,i)=><Skeleton key={i} className="h-8 w-full" />)}</div>
        </div>
      </main>
    </div>
  );

  if (!product) return (
    <div className="min-h-screen page-wrapper hero-bg flex items-center justify-center flex-col gap-4">
      <XCircle className="h-16 w-16 text-slate-400" />
      <h2 className="text-2xl font-bold">Product Not Found</h2>
      <Button onClick={() => navigate("/products")}>Browse Products</Button>
    </div>
  );

  const discountPct = product.discount > 0 ? product.discount : product.originalPrice ? Math.round(((product.originalPrice - product.price) / product.originalPrice) * 100) : 0;
  const originalPrice = product.originalPrice || (discountPct > 0 ? Math.round(product.price / (1 - discountPct / 100)) : null);
  const ratings = product.userRatings || [];
  const avgRating = getAvgRating(product);
  const inStock = (product.stock ?? 100) > 0;

  const handleAddToCart = () => {
    for (let i = 0; i < qty; i++) addToCart(product);
    toast({ title: "Added to cart 🛒", description: `${qty}× ${product.name}` });
  };

  const handleRate = async (rating) => {
    setUserRating(rating);
    const updated = await rateProduct(product.id, rating);
    if (updated) {
      setProduct(updated);
    }
    toast({ title: "Rating submitted ⭐" });
  };

  const handleShare = async () => {
    try { await navigator.share({ title: product.name, url: window.location.href }); }
    catch { navigator.clipboard.writeText(window.location.href); toast({ title: "Link copied!" }); }
  };

  return (
    <div className="min-h-screen page-wrapper hero-bg">
      <Header cartCount={getCartCount()} />
      <main className="page-content container mx-auto px-4 py-8">

        {/* Breadcrumb */}
        <nav className="flex items-center gap-1.5 text-sm text-slate-500 mb-6 flex-wrap font-medium">
          <Link to="/" className="hover:text-blue-600 transition-colors">Home</Link>
          <ChevronRight className="h-3 w-3" />
          <Link to="/products" className="hover:text-blue-600 transition-colors">Products</Link>
          <ChevronRight className="h-3 w-3" />
          <span className="capitalize">{product.category}</span>
          <ChevronRight className="h-3 w-3" />
          <span className="text-slate-900 truncate max-w-[200px] font-semibold">{product.name}</span>
        </nav>

        {/* Layout */}
        <div className="grid lg:grid-cols-2 gap-12 mb-16">
          {/* Image */}
          <div className="space-y-3">
            <div className="relative rounded-3xl overflow-hidden bg-white aspect-square shadow-sm border border-slate-100 glass-card">
              <img src={product.image} alt={product.name} className="w-full h-full object-cover hover:scale-105 transition-transform duration-500 mix-blend-multiply" />
              {discountPct > 0 && <Badge className="absolute top-6 left-6 bg-rose-500 text-white text-sm px-3 py-1 border-none shadow-sm">-{discountPct}% OFF</Badge>}
              {product.isNew && <Badge className="absolute top-6 right-6 bg-emerald-500 text-white text-sm px-3 py-1 border-none shadow-sm">New</Badge>}
            </div>
            <div className="flex flex-wrap gap-2">
              {product.color && <span className="inline-flex items-center gap-1 px-3 py-1.5 rounded-full text-xs border border-border bg-muted/40">🎨 <span className="capitalize">{product.color}</span></span>}
              {product.gender && product.gender !== "unisex" && <span className="inline-flex items-center gap-1 px-3 py-1.5 rounded-full text-xs border border-border bg-muted/40">👤 For <span className="capitalize ml-1">{product.gender}</span></span>}
              <span className="inline-flex items-center gap-1 px-3 py-1.5 rounded-full text-xs border border-border bg-muted/40"><Tag className="h-3 w-3" /><span className="capitalize">{product.category}</span></span>
            </div>
          </div>

          {/* Info */}
          <div className="space-y-5">
            <div>
              <p className="text-sm font-bold text-blue-500 uppercase tracking-widest mb-1">{product.company}</p>
              <h1 className="text-4xl font-bold leading-tight text-slate-900" style={{ fontFamily: "'Plus Jakarta Sans', sans-serif", letterSpacing: "-0.02em" }}>{product.name}</h1>
            </div>

            <div className="flex items-center gap-3">
              <div className="flex items-center gap-0.5">
                {Array.from({length:5}).map((_,i)=>(
                  <Star key={i} className={`h-5 w-5 ${i < Math.round(avgRating) ? "text-amber-400 fill-amber-400" : "text-muted-foreground/30"}`} />
                ))}
              </div>
              <span className="font-semibold">{avgRating.toFixed(1)}</span>
              <span className="text-muted-foreground text-sm">({ratings.length} reviews)</span>
            </div>

            <div className="flex items-baseline gap-3 flex-wrap">
              <span className="text-4xl font-black">{formatPrice(product.price)}</span>
              {originalPrice && discountPct > 0 && (
                <>
                  <span className="text-xl text-muted-foreground line-through">{formatPrice(originalPrice)}</span>
                  <Badge className="bg-green-100 text-green-700">Save {formatPrice(originalPrice - product.price)}</Badge>
                </>
              )}
            </div>

            <div className="flex items-center gap-2 text-sm">
              {inStock ? (
                <><CheckCircle2 className="h-4 w-4 text-emerald-500" /><span className="text-emerald-600 font-medium">In Stock</span>{product.stock <= 10 && <span className="text-amber-600">(Only {product.stock} left!)</span>}</>
              ) : (
                <><XCircle className="h-4 w-4 text-rose-500" /><span className="text-rose-600 font-medium">Out of Stock</span></>
              )}
            </div>

            <div className="flex items-center gap-3">
              <span className="text-sm font-medium text-muted-foreground">Qty:</span>
              <div className="flex items-center border border-border rounded-lg overflow-hidden">
                <button onClick={() => setQty(q => Math.max(1, q-1))} className="px-3 py-2 text-lg hover:bg-muted">−</button>
                <span className="w-10 text-center font-semibold">{qty}</span>
                <button onClick={() => setQty(q => Math.min(product.stock || 10, q+1))} className="px-3 py-2 text-lg hover:bg-muted">+</button>
              </div>
            </div>

            <div className="flex gap-3">
              <Button onClick={handleAddToCart} disabled={!inStock} size="lg" className="flex-1 gap-2 bg-blue-600 hover:bg-blue-700 text-white shadow-md rounded-xl">
                <ShoppingCart className="h-5 w-5" /> Add to Cart
              </Button>
              <Button onClick={() => { if(isInWishlist(product.id)) removeFromWishlist(product.id); else addToWishlist(product); }} size="lg" variant="outline" className={`w-12 h-12 p-0 ${isInWishlist(product.id) ? "text-rose-500 border-rose-300" : ""}`}>
                <Heart className={`h-5 w-5 ${isInWishlist(product.id) ? "fill-current" : ""}`} />
              </Button>
              <Button onClick={handleShare} size="lg" variant="outline" className="w-12 h-12 p-0"><Share2 className="h-5 w-5" /></Button>
            </div>

            <Button onClick={() => { handleAddToCart(); navigate("/cart"); }} disabled={!inStock} size="lg" variant="outline" className="w-full font-bold border-2 border-slate-200 text-slate-800 hover:bg-slate-50 hover:border-blue-300 hover:text-blue-600 rounded-xl transition-all">
              Buy Now →
            </Button>

            <div className="grid grid-cols-3 gap-3">
              {[{icon:"🚚",label:"Free Delivery",sub:"On all orders"},{icon:"🔄",label:"Easy Returns",sub:"7-day policy"},{icon:"🔒",label:"Secure Pay",sub:"100% safe"}].map(h=>(
                <div key={h.label} className="text-center p-3 rounded-2xl bg-white border border-slate-100 shadow-sm">
                  <div className="text-xl mb-1">{h.icon}</div>
                  <p className="text-xs font-bold text-slate-800">{h.label}</p>
                  <p className="text-[10px] text-slate-500 mt-0.5">{h.sub}</p>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="mb-16">
          <div className="flex border-b border-border gap-6 mb-6">
            {["description","reviews"].map(tab=>(
              <button key={tab} onClick={()=>setActiveTab(tab)} className={`pb-3 text-sm font-semibold capitalize ${activeTab===tab?"border-b-2 border-primary text-primary":"text-muted-foreground hover:text-foreground"}`}>
                {tab}{tab==="reviews"?` (${ratings.length})`:""}
              </button>
            ))}
          </div>

          {activeTab === "description" && (
            <div className="text-muted-foreground leading-relaxed">
              <p>{product.description || `Premium ${product.name} by ${product.company}. ${product.color?`Available in ${product.color}.`:""} Experience exceptional quality with this product.`}</p>
              {product.synonyms?.length > 0 && (
                <div className="mt-4 flex flex-wrap gap-2">
                  <span className="text-xs text-muted-foreground font-medium">Also known as:</span>
                  {product.synonyms.map(s=><Badge key={s} variant="outline" className="text-xs capitalize">{s}</Badge>)}
                </div>
              )}
            </div>
          )}

          {activeTab === "reviews" && (
            <div className="space-y-4">
              <div className="flex items-center gap-4 p-4 rounded-xl bg-muted/30 border border-border/50">
                <Sparkles className="h-5 w-5 text-primary flex-shrink-0" />
                <div>
                  <p className="text-sm font-semibold mb-1">Rate this product</p>
                  <div className="flex items-center gap-1">
                    {Array.from({length:5}).map((_,i)=>(
                      <button key={i} onMouseEnter={()=>setHoverRating(i+1)} onMouseLeave={()=>setHoverRating(0)} onClick={()=>handleRate(i+1)} className="hover:scale-110 transition-transform">
                        <Star className={`h-6 w-6 ${i<(hoverRating||userRating)?"text-amber-400 fill-amber-400":"text-muted-foreground/30"}`} />
                      </button>
                    ))}
                  </div>
                </div>
              </div>
              {ratings.length === 0
                ? <p className="text-muted-foreground text-center py-8">No reviews yet — be the first!</p>
                : <div className="grid gap-3 sm:grid-cols-2">{ratings.map((r,i)=><ReviewCard key={i} review={r} index={i} />)}</div>
              }
            </div>
          )}
        </div>

        {similar.length > 0 && (
          <section className="mb-16">
            <h2 className="text-2xl font-bold mb-6">🔍 You Might Also Like</h2>
            {/* The carousel was removed from here. Similar products can be shown later if needed. */}
          </section>
        )}
      </main>

      <footer className="bg-muted/30 mt-16 py-8 border-t">
        <div className="container mx-auto px-4 text-center text-muted-foreground">
          <p>© 2025 Created with ❤️ by <span className="font-semibold text-primary">Harsh Kumar</span></p>
        </div>
      </footer>
    </div>
  );
};

export default ProductDetail;
