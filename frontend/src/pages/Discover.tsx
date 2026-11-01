import { useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { ProductCard } from "../components/ProductCard";
import { Empty, ErrorBox, PageHeader, Spinner } from "../components/ui";
import { useApi } from "../lib/useApi";
import { Category, Product, Scored } from "../types";

export default function Discover() {
  const [sp, setSp] = useSearchParams();
  const [mode, setMode] = useState<"keyword" | "natural">("keyword");
  const [text, setText] = useState(sp.get("q") ?? "");
  const cats = useApi<Category[]>("/api/categories");
  const cat = sp.get("category") ?? "";
  const brands = useApi<string[]>(`/api/brands${cat ? `?category=${cat}` : ""}`);
  const set = (k: string, v: string) => { const n = new URLSearchParams(sp); v ? n.set(k, v) : n.delete(k); if (k === "category") n.delete("brand"); setSp(n); };
  const kwPath = useMemo(() => `/api/products?${sp.toString()}`, [sp]);
  const kw = useApi<Product[]>(mode === "keyword" ? kwPath : null);
  const nl = useApi<Scored[]>(mode === "natural" && sp.get("q") ? `/api/products/semantic?q=${encodeURIComponent(sp.get("q")!)}` : null);
  const loading = mode === "keyword" ? kw.loading : nl.loading;
  const error = mode === "keyword" ? kw.error : nl.error;
  return (
    <>
      <PageHeader title="Discover products" />
      <div className="mb-4 flex flex-wrap gap-2">
        <div className="flex rounded-lg border bg-white p-1 text-sm">{(["keyword", "natural"] as const).map((m) => <button key={m} onClick={() => setMode(m)} className={`rounded-md px-3 py-1 ${mode === m ? "bg-brand-600 text-white" : ""}`}>{m === "keyword" ? "Keyword" : "Natural language"}</button>)}</div>
        <form className="flex flex-1 gap-2" onSubmit={(e) => { e.preventDefault(); set("q", text); }}>
          <input className="input" value={text} onChange={(e) => setText(e.target.value)} placeholder={mode === "keyword" ? "Search name, brand, description" : "e.g. lightweight laptop for coding under 75k"} /><button className="btn">Search</button></form>
      </div>
      <div className="grid gap-6 md:grid-cols-[14rem_1fr]">
        <aside className={`card h-fit space-y-4 text-sm ${mode === "natural" ? "opacity-50" : ""}`}>
          <div><p className="label">Category</p><select className="input" value={cat} onChange={(e) => set("category", e.target.value)} disabled={mode === "natural"}><option value="">All</option>{cats.data?.map((c) => <option key={c.slug} value={c.slug}>{c.name}</option>)}</select></div>
          <div><p className="label">Brand</p><select className="input" value={sp.get("brand") ?? ""} onChange={(e) => set("brand", e.target.value)} disabled={mode === "natural"}><option value="">All</option>{brands.data?.map((b) => <option key={b}>{b}</option>)}</select></div>
          <div><p className="label">Price (₹)</p><div className="flex gap-2"><input className="input" type="number" placeholder="Min" defaultValue={sp.get("min_price") ?? ""} onBlur={(e) => set("min_price", e.target.value)} /><input className="input" type="number" placeholder="Max" defaultValue={sp.get("max_price") ?? ""} onBlur={(e) => set("max_price", e.target.value)} /></div></div>
          <div><p className="label">Sort</p><select className="input" value={sp.get("sort") ?? "relevance"} onChange={(e) => set("sort", e.target.value)}><option value="relevance">Relevance</option><option value="price_asc">Price: low to high</option><option value="price_desc">Price: high to low</option><option value="name">Name</option></select></div>
          {mode === "natural" && <p className="text-xs">Filters are extracted from your sentence in natural-language mode.</p>}
        </aside>
        <div>{loading ? <Spinner /> : error ? <ErrorBox msg={error} /> : mode === "keyword" ? (
          kw.data?.length ? <div className="grid grid-cols-2 gap-4 lg:grid-cols-3">{kw.data.map((p) => <ProductCard key={p.id} p={p} />)}</div> : <Empty title="No products match" hint="Try removing a filter." />
        ) : !sp.get("q") ? <Empty title="Describe what you need" /> : nl.data?.length ? <div className="grid grid-cols-2 gap-4 lg:grid-cols-3">{nl.data.map((r) => <ProductCard key={r.product.id} p={r.product} reasons={r.reasons} score={r.score} />)}</div> : <Empty title="No products match those constraints" />}</div>
      </div>
    </>
  );
}
