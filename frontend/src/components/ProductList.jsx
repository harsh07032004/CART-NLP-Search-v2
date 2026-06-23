import { useState } from "react";
import { Edit, Trash2, Package } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ProductCard } from "./ProductCard";

export function ProductList({ products, onEdit, onDelete }) {
  const [deletingId, setDeletingId] = useState(null);

  const handleDelete = async (product) => {
    setDeletingId(product.id);
    try {
      await onDelete(product.id);
    } finally {
      setDeletingId(null);
    }
  };

  if (products.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <Package className="h-16 w-16 text-muted-foreground mb-4 opacity-50" />
        <h3 className="text-xl font-semibold mb-2">No Products Yet</h3>
        <p className="text-muted-foreground">Click "Add Product" to add your first product.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-2">
        <h2 className="text-2xl font-semibold">
          Products{" "}
          <span className="text-muted-foreground text-lg font-normal">
            ({products.length})
          </span>
        </h2>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {products.map((product) => (
          <div key={product.id} className="flex flex-col gap-2">
            <div className="flex-1">
              <ProductCard product={product} onAddToCart={() => {}} />
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                className="flex-1 gap-2"
                onClick={() => onEdit(product)}
              >
                <Edit className="h-4 w-4 text-blue-600" /> Edit
              </Button>
              <Button
                variant="destructive"
                size="sm"
                className="flex-1 gap-2"
                disabled={deletingId === product.id}
                onClick={() => handleDelete(product)}
              >
                {deletingId === product.id ? (
                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                ) : (
                  <>
                    <Trash2 className="h-4 w-4" /> Delete
                  </>
                )}
              </Button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
