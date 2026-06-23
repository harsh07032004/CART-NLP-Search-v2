import { useState } from "react";
import { Plus } from "lucide-react";
import { Header } from "@/components/Header";
import { Button } from "@/components/ui/button";
import { ProductForm } from "@/components/ProductForm";
import { ProductList } from "@/components/ProductList";
import { useProducts } from "@/contexts/ProductsContext";

const AddProduct = () => {
  const { products, addProduct, updateProduct, deleteProduct } = useProducts();
  const [editingProduct, setEditingProduct] = useState(null);
  const [showForm, setShowForm] = useState(false);

  const handleAddProduct = async (productData) => {
    try {
      await addProduct(productData);
      setShowForm(false);
    } catch {
      // addProduct already shows toast on error
    }
  };

  const handleUpdateProduct = async (productData) => {
    if (!editingProduct) return;
    try {
      await updateProduct(editingProduct.id, productData);
      setEditingProduct(null);
      setShowForm(false);
    } catch {
      // updateProduct already shows toast on error
    }
  };

  const handleDeleteProduct = async (productId) => {
    const product = products.find((p) => p.id === productId);
    if (!window.confirm(`Delete "${product?.name}"? This cannot be undone.`)) return;
    await deleteProduct(productId);
  };

  const handleEditProduct = (product) => {
    setEditingProduct(product);
    setShowForm(true);
  };

  return (
    <div className="min-h-screen bg-background">
      <Header onSearch={() => {}} cartCount={0} />

      <main className="container mx-auto px-4 py-24">
        <div className="mb-8 border-b pb-6">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <h1 className="text-3xl font-bold">Add Product For Testing</h1>
              <p className="text-muted-foreground mt-1">
                Add products here to test the NLP search engine. Anyone can add or edit products in this demo mode.
              </p>
            </div>

            {!showForm && (
              <Button onClick={() => setShowForm(true)} className="gap-2 shrink-0">
                <Plus className="h-4 w-4" />
                Add New Product
              </Button>
            )}
          </div>
        </div>

        {showForm ? (
          <ProductForm
            product={editingProduct}
            onSubmit={editingProduct ? handleUpdateProduct : handleAddProduct}
            onCancel={() => { setShowForm(false); setEditingProduct(null); }}
          />
        ) : (
          <ProductList
            products={products}
            onEdit={handleEditProduct}
            onDelete={handleDeleteProduct}
          />
        )}
      </main>
    </div>
  );
};

export default AddProduct;