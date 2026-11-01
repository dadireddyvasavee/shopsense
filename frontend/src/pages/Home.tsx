import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ProductCard } from "../components/ProductCard";
import { Empty, ErrorBox, Spinner } from "../components/ui";
import { useAuth } from "../lib/auth";
import { useApi } from "../lib/useApi";
import { Comparison, Product, Scored } from "../types";

const Row = ({ title, items, to }: { title: string; items: Product[]; to?: string }) => (
  <section className="mt-8"><div className="mb-3 flex justify-between"><h2 className="text-lg font-semibold">{title}</h2>{to && <Link to={to} className="text-sm text-brand-600">View all</Link>}</div>
    {items.length ? <div className="grid grid-cols-2 gap-4 md:grid-cols-4">{items.slice(0, 4).map((p) => <ProductCard key={p.id} p={p} />)}</div> : <Empty title="Nothing here yet" />}</section>
);

export default function Home() {
  const { user } = useAuth();
  const nav = useNavigate();
  const [q, setQ] = useState("");
  const recs = useApi<Scored[]>("/api/me/recommendations?limit=8");
  const history = useApi<Product[]>("/api/me/history");
  const saved = useApi<Product[]>("/api/me/saved");
  const cats = useApi<{ slug: string; name: string; interactions: number }[]>("/api/stats/popular-categories");
  const cmp = useApi<Comparison[]>("/api/compare/history");
  const ask = (e: FormEvent) => { e.preventDefault(); if (q.trim()) nav(`/app/assistant?q=${encodeURIComponent(q)}`); };
  return (
    <>
      <div className="rounded-2xl bg-gradient-to-r from-brand-600 to-emerald-500 p-6 text-white">
        <p className="text-sm opacity-80">Hi {user?.full_name?.split(" ")[0]} 👋</p>
        <h1 className="mt-1 text-2xl font-semibold">What are you shopping for today?</h1>
        <form onSubmit={ask} className="mt-4 flex gap-2"><input className="input text-slate-900" placeholder="e.g. noise cancelling headphones under 10k for work" value={q} onChange={(e) => setQ(e.target.value)} /><button className="btn-ghost">Ask AI</button></form>
      </div>
      <div className="mt-6 flex flex-wrap gap-2">{cats.data?.map((c) => <Link key={c.slug} to={`/app/discover?category=${c.slug}`} className="rounded-full border bg-white px-4 py-1.5 text-sm hover:border-brand-500">{c.name} <span className="text-xs text-slate-400">{c.interactions}</span></Link>)}</div>
      <section className="mt-8"><h2 className="mb-3 text-lg font-semibold">Recommended for you</h2>
        {recs.loading ? <Spinner /> : recs.error ? <ErrorBox msg={recs.error} /> :
          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">{recs.data!.map((r) => <ProductCard key={r.product.id} p={r.product} reasons={r.reasons} score={r.score} />)}</div>}
        <p className="mt-2 text-xs text-slate-500">Set your budget and favourites in <Link to="/app/profile" className="text-brand-600">Profile</Link> to sharpen these.</p></section>
      <Row title="Recently viewed" items={history.data ?? []} />
      <Row title="Saved products" items={saved.data ?? []} to="/app/saved" />
      <section className="mt-8"><h2 className="mb-3 text-lg font-semibold">Your comparisons</h2>
        {cmp.data?.length ? <ul className="space-y-2">{cmp.data.slice(0, 5).map((c) => <li key={c.id} className="card py-3 text-sm"><Link to={`/app/compare?ids=${c.products.map((p) => p.id).join(",")}`} className="text-brand-600">{c.products.map((p) => p.name).join(" vs ")}</Link></li>)}</ul> : <Empty title="No comparisons yet" />}</section>
    </>
  );
}
