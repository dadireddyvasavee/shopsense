import { ProductCard } from "../components/ProductCard";
import { Empty, PageHeader, Spinner } from "../components/ui";
import { api } from "../lib/api";
import { useApi } from "../lib/useApi";
import { Product, Scored } from "../types";

export default function Saved() {
  const saved = useApi<Product[]>("/api/me/saved");
  const recs = useApi<(Scored & { id: number; context: string })[]>("/api/me/recommendations/saved");
  const remove = async (id: number) => { await api(`/api/me/saved/${id}`, { method: "DELETE" }); saved.reload(); };
  return (
    <>
      <PageHeader title="Saved products" />
      {saved.loading ? <Spinner /> : !saved.data?.length ? <Empty title="No saved products" hint="Use ♡ Save on a product page." /> :
        <div className="grid grid-cols-2 gap-4 md:grid-cols-4">{saved.data.map((p) => <div key={p.id}><ProductCard p={p} /><button onClick={() => remove(p.id)} className="mt-1 w-full text-xs text-red-600">Remove</button></div>)}</div>}
      <h2 className="mb-3 mt-10 text-lg font-semibold">Saved recommendations</h2>
      {recs.data?.length ? <div className="grid grid-cols-2 gap-4 md:grid-cols-4">{recs.data.map((r) => <ProductCard key={r.id} p={r.product} reasons={r.reasons} score={r.score} />)}</div> : <Empty title="No saved recommendations" hint="Save picks from the AI assistant." />}
    </>
  );
}
