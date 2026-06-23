import { useState, useEffect } from "react";
import { Search, ShoppingCart, Menu, X, Plus, Zap } from "lucide-react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useDebounce } from "@/hooks/useDebounce";

export function Header({ onSearch, cartCount }) {
  const [searchQuery, setSearchQuery] = useState("");
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isScrolled, setIsScrolled] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const debouncedQuery = useDebounce(searchQuery, 350);

  useEffect(() => {
    const handleScroll = () => setIsScrolled(window.scrollY > 12);
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  useEffect(() => {
    if (debouncedQuery.trim()) {
      if (location.pathname !== "/products") {
        navigate(`/products?search=${encodeURIComponent(debouncedQuery.trim())}`);
      } else if (typeof onSearch === "function") {
        onSearch(debouncedQuery.trim());
      }
    }
  }, [debouncedQuery]); // eslint-disable-line

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchQuery.trim()) navigate(`/products?search=${encodeURIComponent(searchQuery.trim())}`);
  };

  return (
    <header className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${isScrolled ? "bg-white/80 backdrop-blur-md shadow-sm py-3" : "py-4 bg-transparent"}`}>
      <div className="mx-auto max-w-7xl px-6">
        <div className="flex items-center justify-between h-12">
          
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2">
            <div className="relative w-8 h-8 rounded-xl overflow-hidden flex items-center justify-center bg-blue-600">
              <Zap className="h-4 w-4 text-white fill-white" />
            </div>
            <span className="text-lg font-black tracking-tight text-gray-900" style={{ fontFamily: "'Syne', sans-serif" }}>CART</span>
          </Link>

          {/* Desktop Nav */}
          <nav className="hidden lg:flex items-center gap-4">
            <Link to="/" className="text-sm font-medium text-gray-700 hover:text-blue-600">Home</Link>
            <Link to="/products" className="text-sm font-medium text-gray-700 hover:text-blue-600">Shop</Link>
          </nav>

          {/* Right Actions */}
          <div className="hidden md:flex items-center gap-4">
            
            {/* Search Bar */}
            <form onSubmit={handleSearch} className="relative hidden lg:block">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9 pr-4 py-1.5 rounded-full text-sm border border-gray-200 bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 w-48"
              />
            </form>

            <Link to="/add-product" className="flex items-center gap-1.5 px-4 py-1.5 rounded-full text-sm font-medium bg-amber-100 text-amber-700 hover:bg-amber-200 transition-colors border border-amber-200 shadow-sm" title="Add Product for Testing">
              <Plus className="h-4 w-4" /> Add Product (Test)
            </Link>

            <Link to="/cart" className="relative flex items-center justify-center h-10 w-10 rounded-full bg-gray-100 hover:bg-gray-200 transition-colors text-gray-700">
              <ShoppingCart className="h-5 w-5" />
              {cartCount > 0 && (
                <span className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-blue-600 text-white text-[10px] font-bold flex items-center justify-center shadow-md">
                  {cartCount}
                </span>
              )}
            </Link>
          </div>

          {/* Mobile Toggle */}
          <div className="md:hidden flex items-center gap-3">
            <Link to="/cart" className="relative text-gray-700">
              <ShoppingCart className="h-6 w-6" />
              {cartCount > 0 && (
                <span className="absolute -top-2 -right-2 w-5 h-5 rounded-full bg-blue-600 text-white text-[10px] font-bold flex items-center justify-center">
                  {cartCount}
                </span>
              )}
            </Link>
            <button onClick={() => setIsMenuOpen(!isMenuOpen)} className="text-gray-700">
              {isMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Menu */}
      {isMenuOpen && (
        <div className="md:hidden absolute top-full left-0 right-0 bg-white border-b border-gray-100 shadow-lg p-4 flex flex-col gap-4">
          <form onSubmit={handleSearch} className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input type="text" placeholder="Search..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} className="w-full pl-9 pr-4 py-2 rounded-lg border border-gray-200 bg-gray-50 focus:outline-none" />
          </form>
          <Link to="/" onClick={() => setIsMenuOpen(false)} className="text-sm font-medium text-gray-700 py-2 border-b">Home</Link>
          <Link to="/products" onClick={() => setIsMenuOpen(false)} className="text-sm font-medium text-gray-700 py-2 border-b">Shop</Link>
          <Link to="/add-product" onClick={() => setIsMenuOpen(false)} className="flex items-center gap-2 text-sm font-medium text-amber-600 py-2">
            <Plus className="h-4 w-4" /> Add Product (Test)
          </Link>
        </div>
      )}
    </header>
  );
}