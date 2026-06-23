/**
 * SmartSearchBar — The flagship NLP showcase component.
 *
 * Upgraded Features:
 * - ✅ Animated typewriter placeholder cycling through vivid example queries
 * - ✅ Glowing ring animation when focused
 * - ✅ Real-time autocomplete dropdown (entity + product hints from backend)
 * - ✅ Voice Search via Web Speech API (microphone button)
 * - ✅ Real entity chips from backend /search/parse (not hardcoded)
 * - ✅ "Did you mean?" correction prompt
 * - ✅ Sort intent badge (e.g. "Sorting: cheapest first")
 * - ✅ Quick-example chips for instant tryouts
 * - ✅ Full keyboard navigation in autocomplete dropdown
 */

import { useState, useEffect, useRef, useCallback } from "react";
import { Search, Sparkles, X, Loader2, Mic, MicOff, Tag, Store, ArrowRight, RefreshCw } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useProducts } from "@/contexts/ProductsContext";
import { api } from "@/lib/api";
import { useDebounce } from "@/hooks/useDebounce";
import { formatPrice } from "@/lib/utils";

// ── Entity chip config ────────────────────────────────────────────────────────
const ENTITY_CONFIG = {
  category:    { label: "Category",  emoji: "🏷️",  color: "from-violet-500 to-purple-600" },
  brand:       { label: "Brand",     emoji: "✨",   color: "from-blue-500 to-cyan-500" },
  color:       { label: "Color",     emoji: "🎨",  color: "from-pink-500 to-rose-500" },
  gender:      { label: "For",       emoji: "👤",  color: "from-amber-500 to-orange-500" },
  price_max:   { label: "Under",     emoji: "💰",  color: "from-green-500 to-emerald-500" },
  price_min:   { label: "Above",     emoji: "💎",  color: "from-teal-500 to-green-400" },
  sort_by:     { label: "Sort",      emoji: "↕️",  color: "from-slate-500 to-gray-600" },
  min_discount:{ label: "Min. Off",  emoji: "🏷️",  color: "from-orange-500 to-red-500" },
};

const SORT_LABELS = {
  price_asc:     "Cheapest first",
  price_desc:    "Most expensive",
  rating_desc:   "Best rated",
  discount_desc: "Biggest discount",
  newest:        "Newest first",
};

// ── Example queries ───────────────────────────────────────────────────────────
const EXAMPLE_QUERIES = [
  { text: "red Nike shoes for men under ₹3000" },
  { text: "50% off jackets" },
  { text: "blue shirts for men" },
  { text: "Levis jeans for women" },
  { text: "boat earphones below ₹800" },
  { text: "best rated Samsung phones" },
  { text: "laptop under ₹50000" },
  { text: "navy jackets on sale" },
  { text: "samusng phone" },
  { text: "cheapest Adidas shoes" },
];

// ── Typewriter hook ───────────────────────────────────────────────────────────
function useTypewriter(texts, pause = 1800) {
  const [displayText, setDisplayText] = useState("");
  const [currentIdx, setCurrentIdx] = useState(0);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    const target = texts[currentIdx];
    let timeout;
    if (!isDeleting) {
      if (displayText.length < target.length) {
        timeout = setTimeout(() => setDisplayText(target.slice(0, displayText.length + 1)), 55);
      } else {
        timeout = setTimeout(() => setIsDeleting(true), pause);
      }
    } else {
      if (displayText.length > 0) {
        timeout = setTimeout(() => setDisplayText(displayText.slice(0, -1)), 28);
      } else {
        setIsDeleting(false);
        setCurrentIdx((i) => (i + 1) % texts.length);
      }
    }
    return () => clearTimeout(timeout);
  }, [displayText, isDeleting, currentIdx, texts, pause]);

  return displayText;
}

// ── Entity Chips ──────────────────────────────────────────────────────────────
function EntityChip({ type, value }) {
  const cfg = ENTITY_CONFIG[type];
  if (!cfg || value === null || value === undefined || value === false) return null;

  let displayVal = value;
  if (type === "price_max" || type === "price_min") displayVal = formatPrice(value);
  else if (type === "sort_by") displayVal = SORT_LABELS[value] || value;
  else if (type === "min_discount") displayVal = `${value}%+`;

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold text-white bg-gradient-to-r ${cfg.color} shadow-sm`}
    >
      <span>{cfg.emoji}</span>
      <span className="opacity-80">{cfg.label}:</span>
      <span className="capitalize">{displayVal}</span>
    </span>
  );
}

// ── Voice Search Hook ─────────────────────────────────────────────────────────
function useVoiceSearch(onResult) {
  const [isListening, setIsListening] = useState(false);
  const [isSupported] = useState(() => "webkitSpeechRecognition" in window || "SpeechRecognition" in window);
  const recognitionRef = useRef(null);

  const startListening = useCallback(() => {
    if (!isSupported) return;
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.lang = "en-IN";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onstart = () => setIsListening(true);
    recognition.onend = () => setIsListening(false);
    recognition.onerror = () => setIsListening(false);
    recognition.onresult = (e) => {
      const transcript = e.results[0][0].transcript;
      onResult(transcript);
    };

    recognitionRef.current = recognition;
    recognition.start();
  }, [isSupported, onResult]);

  const stopListening = useCallback(() => {
    recognitionRef.current?.stop();
    setIsListening(false);
  }, []);

  return { isListening, isSupported, startListening, stopListening };
}

// ── Main Component ────────────────────────────────────────────────────────────
export function SmartSearchBar({ className = "" }) {
  const [query, setQuery] = useState("");
  const [isFocused, setIsFocused] = useState(false);
  const [parsedEntities, setParsedEntities] = useState(null);
  const [didYouMean, setDidYouMean] = useState(null);
  const [autocomplete, setAutocomplete] = useState({ suggestions: [], products: [] });
  const [showDropdown, setShowDropdown] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const [isParsing, setIsParsing] = useState(false);

  const inputRef = useRef(null);
  const dropdownRef = useRef(null);
  const navigate = useNavigate();
  const { searchProducts, isSearching } = useProducts();

  const debouncedQuery = useDebounce(query, 180);       // autocomplete debounce
  const debouncedParse = useDebounce(query, 600);       // parse debounce (heavier)

  const exampleTexts = EXAMPLE_QUERIES.map((q) => q.text);
  const typewriterText = useTypewriter(exampleTexts);

  // ── Real-time autocomplete ──────────────────────────────────────────────────
  useEffect(() => {
    if (!debouncedQuery.trim() || debouncedQuery.trim().length < 2) {
      setAutocomplete({ suggestions: [], products: [] });
      setShowDropdown(false);
      return;
    }
    api.autocomplete(debouncedQuery).then((data) => {
      setAutocomplete(data);
      setShowDropdown(
        (data.suggestions?.length > 0 || data.products?.length > 0) && isFocused
      );
      setActiveIndex(-1);
    });
  }, [debouncedQuery]); // eslint-disable-line

  // ── Real-time entity parse ──────────────────────────────────────────────────
  useEffect(() => {
    if (!debouncedParse.trim() || debouncedParse.trim().length < 3) {
      setParsedEntities(null);
      setDidYouMean(null);
      return;
    }
    setIsParsing(true);
    api.parseQuery(debouncedParse)
      .then(({ parsed }) => {
        const relevant = {};
        ["category", "brand", "color", "gender", "price_max", "price_min", "sort_by", "min_discount"]
          .forEach((k) => { if (parsed[k]) relevant[k] = parsed[k]; });
        setParsedEntities(Object.keys(relevant).length > 0 ? relevant : null);
        setDidYouMean(parsed.did_you_mean || null);
      })
      .catch(() => {})
      .finally(() => setIsParsing(false));
  }, [debouncedParse]);

  // ── Search handler ──────────────────────────────────────────────────────────
  const handleSearch = useCallback(
    async (searchQuery) => {
      const q = (searchQuery ?? query).trim();
      if (!q) return;
      setShowDropdown(false);
      await searchProducts(q);
      navigate(`/products?search=${encodeURIComponent(q)}`);
    },
    [query, searchProducts, navigate]
  );

  // ── Voice search ────────────────────────────────────────────────────────────
  const { isListening, isSupported: voiceSupported, startListening, stopListening } =
    useVoiceSearch((transcript) => {
      setQuery(transcript);
      handleSearch(transcript);
    });

  // ── Keyboard navigation in dropdown ────────────────────────────────────────
  const allItems = [
    ...(autocomplete.suggestions || []).map((s) => ({ kind: "suggestion", ...s })),
    ...(autocomplete.products || []).map((p) => ({ kind: "product", ...p })),
  ];

  const handleKeyDown = (e) => {
    if (!showDropdown) {
      if (e.key === "Enter") handleSearch();
      return;
    }
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActiveIndex((i) => Math.min(i + 1, allItems.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActiveIndex((i) => Math.max(i - 1, -1));
    } else if (e.key === "Enter") {
      if (activeIndex >= 0 && allItems[activeIndex]) {
        const item = allItems[activeIndex];
        const text = item.kind === "suggestion" ? item.text : item.name;
        setQuery(text);
        setShowDropdown(false);
        handleSearch(text);
      } else {
        handleSearch();
      }
    } else if (e.key === "Escape") {
      setShowDropdown(false);
    }
  };

  const handleClear = () => {
    setQuery("");
    setParsedEntities(null);
    setDidYouMean(null);
    setAutocomplete({ suggestions: [], products: [] });
    setShowDropdown(false);
    inputRef.current?.focus();
  };

  // ── Close dropdown on outside click ────────────────────────────────────────
  useEffect(() => {
    const handleOutside = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setShowDropdown(false);
      }
    };
    document.addEventListener("mousedown", handleOutside);
    return () => document.removeEventListener("mousedown", handleOutside);
  }, []);

  return (
    <div className={`w-full max-w-3xl mx-auto ${className}`}>
      {/* ── Search Input ── */}
      <div
        ref={dropdownRef}
        className={`relative rounded-2xl transition-all duration-300 ${
          isFocused
            ? "ring-blue shadow-[0_4px_32px_hsl(214_100%_60%/0.18)]"
            : ""
        }`}
      >
        <div className="flex items-center bg-white border-2 border-gray-200 rounded-2xl overflow-hidden transition-all duration-300 hover:border-blue-300 focus-within:border-blue-500 focus-within:shadow-[0_0_0_4px_rgba(29,107,240,0.10)]">
          {/* Icon */}
          <div className="pl-5 pr-3 flex-shrink-0">
            {isSearching || isParsing ? (
              <Loader2 className="h-5 w-5 text-primary animate-spin" />
            ) : (
              <Sparkles className="h-5 w-5 text-primary" />
            )}
          </div>

          {/* Input */}
          <input
            ref={inputRef}
            id="smart-search-input"
            type="text"
            value={query}
            onChange={(e) => { setQuery(e.target.value); setShowDropdown(true); }}
            onFocus={() => { setIsFocused(true); if (autocomplete.suggestions?.length > 0) setShowDropdown(true); }}
            onBlur={() => setIsFocused(false)}
            onKeyDown={handleKeyDown}
            placeholder={isFocused || query ? "" : typewriterText}
            className="flex-1 h-14 bg-transparent text-foreground placeholder:text-muted-foreground/50 text-base outline-none font-medium"
            autoComplete="off"
            aria-label="Search products"
            aria-autocomplete="list"
            aria-controls="search-autocomplete-list"
            aria-expanded={showDropdown}
          />

          {/* Typewriter cursor */}
          {!isFocused && !query && (
            <span className="text-primary/60 font-light text-xl animate-pulse mr-2 select-none">|</span>
          )}

          {/* Voice search */}
          {voiceSupported && (
            <button
              type="button"
              onClick={isListening ? stopListening : startListening}
              title={isListening ? "Stop listening" : "Search by voice"}
              className={`px-3 transition-colors ${
                isListening ? "text-rose-500 animate-pulse" : "text-muted-foreground hover:text-primary"
              }`}
            >
              {isListening ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
            </button>
          )}

          {/* Clear */}
          {query && (
            <button
              type="button"
              onClick={handleClear}
              className="px-3 text-muted-foreground hover:text-foreground transition-colors"
            >
              <X className="h-4 w-4" />
            </button>
          )}

          {/* Search Button */}
          <button
            id="smart-search-button"
            onClick={() => handleSearch()}
            disabled={isSearching}
            className="flex-shrink-0 h-14 px-6 bg-blue-600 hover:bg-blue-700 text-white font-semibold flex items-center gap-2 transition-all duration-200 disabled:opacity-60 rounded-r-xl"
          >
            <Search className="h-4 w-4" />
            <span className="hidden sm:inline">Search</span>
          </button>
        </div>

        {/* ── Autocomplete Dropdown ── */}
        {showDropdown && allItems.length > 0 && (
          <div
            id="search-autocomplete-list"
            role="listbox"
            className="absolute top-full left-0 right-0 mt-2 bg-white/98 backdrop-blur-xl border border-gray-200 shadow-[0_16px_48px_rgba(29,107,240,0.16)] rounded-2xl z-50 overflow-hidden animate-slide-down"
          >
            {autocomplete.suggestions?.length > 0 && (
              <div>
                <p className="px-4 pt-3 pb-1 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  Suggestions
                </p>
                {autocomplete.suggestions.map((s, idx) => (
                  <button
                    key={`s-${idx}`}
                    role="option"
                    aria-selected={activeIndex === idx}
                    onClick={() => { setQuery(s.text); handleSearch(s.text); }}
                    className={`w-full flex items-center gap-3 px-4 py-2.5 text-left hover:bg-accent transition-colors ${
                      activeIndex === idx ? "bg-accent" : ""
                    }`}
                  >
                    {s.type === "brand" ? (
                      <Store className="h-4 w-4 text-primary flex-shrink-0" />
                    ) : (
                      <Tag className="h-4 w-4 text-primary/70 flex-shrink-0" />
                    )}
                    <span className="capitalize text-sm font-medium">{s.text}</span>
                    <span className="ml-auto badge badge-blue text-[10px]">{s.type}</span>
                  </button>
                ))}
              </div>
            )}

            {autocomplete.products?.length > 0 && (
              <div className="border-t border-border">
                <p className="px-4 pt-3 pb-1 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  Products
                </p>
                {autocomplete.products.map((p, idx) => {
                  const i = (autocomplete.suggestions?.length || 0) + idx;
                  return (
                    <button
                      key={`p-${idx}`}
                      role="option"
                      aria-selected={activeIndex === i}
                      onClick={() => { setQuery(p.name); handleSearch(p.name); }}
                      className={`w-full flex items-center gap-3 px-4 py-2.5 text-left hover:bg-accent transition-colors ${
                        activeIndex === i ? "bg-accent" : ""
                      }`}
                    >
                      <img
                        src={p.image || "https://placehold.co/32x32?text=•"}
                        alt={p.name}
                        className="w-9 h-9 rounded-xl object-cover flex-shrink-0 border border-border"
                      />
                      <div className="min-w-0">
                        <p className="text-sm font-semibold truncate">{p.name}</p>
                        <p className="text-xs text-muted-foreground capitalize">{p.brand} · {p.category}</p>
                      </div>
                      <span className="ml-auto text-sm font-bold text-foreground">{formatPrice(p.price)}</span>
                    </button>
                  );
                })}
              </div>
            )}

            <div className="px-4 py-3 border-t border-border flex items-center justify-between bg-secondary/30">
              <span className="text-xs text-muted-foreground">↑↓ navigate · Enter select · Esc close</span>
              <button
                onClick={() => handleSearch()}
                className="text-xs text-primary font-semibold flex items-center gap-1 hover:underline"
              >
                See all results <ArrowRight className="h-3 w-3" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* ── Did You Mean ── */}
      {didYouMean && (
        <div className="mt-2 flex items-center gap-2 text-sm animate-fade-in">
          <RefreshCw className="h-3.5 w-3.5 text-amber-500" />
          <span className="text-muted-foreground">Did you mean:</span>
          <button
            onClick={() => { setQuery(didYouMean); handleSearch(didYouMean); setDidYouMean(null); }}
            className="text-primary font-medium hover:underline italic"
          >
            {didYouMean}
          </button>
        </div>
      )}

      {/* ── AI Parsed Entities ── */}
      {parsedEntities && Object.keys(parsedEntities).length > 0 && (
        <div className="mt-3 flex flex-wrap items-center gap-2 animate-fade-in">
          <span className="text-xs font-medium text-muted-foreground flex items-center gap-1">
            <Sparkles className="h-3 w-3 text-primary" />
            AI understood:
          </span>
          {Object.entries(parsedEntities).map(([key, val]) => (
            <EntityChip key={key} type={key} value={val} />
          ))}
        </div>
      )}

      {/* ── Voice Listening Indicator ── */}
      {isListening && (
        <div className="mt-2 flex items-center gap-2 text-sm text-red-500 animate-pulse">
          <Mic className="h-4 w-4" />
          <span>Listening… speak your search query</span>
        </div>
      )}

      {/* ── Quick Example Chips ── */}
      <div className="mt-4 flex flex-wrap gap-2">
        <span className="text-xs text-muted-foreground self-center font-medium">Try:</span>
        {EXAMPLE_QUERIES.slice(0, 5).map((ex, i) => (
          <button
            key={i}
            onClick={() => { setQuery(ex.text); handleSearch(ex.text); }}
            className="cat-chip text-xs py-1 px-3"
          >
            <Sparkles className="h-3 w-3 text-primary/60" />
            {ex.text}
          </button>
        ))}
      </div>
    </div>
  );
}

export { EXAMPLE_QUERIES };
