import { useState } from "react";
import { useParams } from "react-router-dom";
import { inr, ProductCard, ProductImage } from "../components/ProductCard";
import { Badge, ErrorBox, Spinner } from "../components/ui";
import { api } from "../lib/api";
import { useCompareTray } from "../lib/compareTray";
import { useApi } from "../lib/useApi";
import { Product } from "../types";

export default function ProductDetail() {
  const { id } = useParams();
  const { data: p, loading, error } = useApi<Product>(`/api/products/${id}`);
  const similar = useApi<Product[]>(`/api/products/${id}/similar`);
  const tray = useCompareTray();
  const [note, setNote] = useState<string | null>(null);
  if (loading) return <Spinner />;
  if (error || !p) return <ErrorBox msg={error ?? "Not found"} />;
  const act = async (fn: () => Promise<unknown>, msg: string) => { try { await fn(); setNote(msg); } catch (e) { setNote((e as Error).message); } };
  return (
    <>
      <div className="grid gap-8 md:grid-cols-2">
        <ProductImage p={p} big />
        <div>
          <p className="text-sm text-slate-500">{p.brand} · {p.category.name} · {p.sku} <Badge tone="amber">{p.source} data</Badge></p>
          <h1 className="mt-1 text-3xl font-semibold">{p.name}</h1>
          <p className="mt-3 text-2xl font-bold">{inr(p.price)}</p>
          <p className="mt-4 text-slate-700">{p.description}</p>
          <div className="mt-4 flex flex-wrap gap-1">{p.attributes.map((a) => <Badge key={a} tone="brand">{a}</Badge>)}</div>
          <div className="mt-6 flex flex-wrap gap-2">
            <button className="btn" onClick={() => act(() => api(`/api/me/saved/${p.id}`, { method: "POST" }), "Saved ✓")}>♡ Save</button>
            <button className="btn-ghost" onClick={() => tray.toggle(p.id)}>{tray.ids.includes(p.id) ? "Remove from compare" : "Add to compare"}</button>
            <button className="btn-ghost" onClick={() => act(() => api(`/api/products/${p.id}/feedback`, { method: "POST", json: { kind: "like" } }), "We'll show more like this")}>👍 More like this</button>
            <button className="btn-ghost" onClick={() => act(() => api(`/api/products/${p.id}/feedback`, { method: "POST", json: { kind: "dislike" } }), "We'll show less like this")}>👎 Not for me</button>
          </div>
          {note && <p className="mt-2 text-sm text-slate-500">{note}</p>}
          <table className="mt-6 w-full text-sm"><tbody className="divide-y">{Object.entries(p.specifications).map(([k, v]) => <tr key={k}><td className="py-2 capitalize text-slate-500">{k.replace(/_/g, " ")}</td><td className="py-2 font-medium">{String(v)}</td></tr>)}</tbody></table>
        </div>
      </div>
      {!!similar.data?.length && <section className="mt-10"><h2 className="mb-3 text-lg font-semibold">Similar products</h2><div className="grid grid-cols-2 gap-4 md:grid-cols-4">{similar.data.map((s) => <ProductCard key={s.id} p={s} />)}</div></section>}
    </>
  );
}
