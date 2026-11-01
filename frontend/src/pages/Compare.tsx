import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { inr, ProductImage } from "../components/ProductCard";
import { Empty, ErrorBox, PageHeader, Spinner } from "../components/ui";
import { api } from "../lib/api";
import { useCompareTray } from "../lib/compareTray";
import { useApi } from "../lib/useApi";
import { Comparison, Prefs } from "../types";

export default function Compare() {
  const [sp] = useSearchParams();
  const tray = useCompareTray();
  const ids = sp.get("ids")?.split(",").map(Number) ?? tray.ids;
  const prefs = useApi<Prefs>("/api/me/preferences");
  const history = useApi<Comparison[]>("/api/compare/history");
  const [c, setC] = useState<Comparison | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const key = ids.join(",");
  useEffect(() => {
    if (ids.length < 2) { setC(null); return; }
    setBusy(true); setErr(null);
    api<Comparison>("/api/compare", { method: "POST", json: { product_ids: ids } }).then((r) => { setC(r); history.reload(); }).catch((e) => setErr(e.message)).finally(() => setBusy(false));
  }, [key]); // eslint-disable-line react-hooks/exhaustive-deps
  const budget = prefs.data?.budget_max;
  return (
    <>
      <PageHeader title="Compare products">{tray.ids.length > 0 && <button className="btn-ghost" onClick={tray.clear}>Clear selection</button>}</PageHeader>
      {ids.length < 2 ? <Empty title="Select 2–4 products to compare" hint="Tick “Compare” on any product card." /> : busy ? <Spinner /> : err ? <ErrorBox msg={err} /> : c && <>
        <div className="card overflow-x-auto p-0"><table className="w-full text-sm">
          <thead><tr><th className="th w-40" />{c.products.map((p) => <th key={p.id} className="p-3 text-left align-top"><ProductImage p={p} /><Link to={`/app/products/${p.id}`} className="mt-2 block font-semibold text-brand-700">{p.name}</Link></th>)}</tr></thead>
          <tbody className="divide-y">
            <tr><td className="td font-medium">Price</td>{c.products.map((p) => <td key={p.id} className="td font-semibold">{inr(p.price)} {budget && <span className={`ml-1 text-xs ${p.price <= budget ? "text-emerald-600" : "text-red-500"}`}>{p.price <= budget ? "within your budget" : "over budget"}</span>}</td>)}</tr>
            <tr><td className="td font-medium">Brand / category</td>{c.products.map((p) => <td key={p.id} className="td">{p.brand} · {p.category.name}</td>)}</tr>
            {c.spec_keys.map((k) => <tr key={k}><td className="td capitalize text-slate-500">{k.replace(/_/g, " ")}</td>{c.products.map((p) => <td key={p.id} className="td">{p.specifications[k] === undefined ? "—" : String(p.specifications[k])}</td>)}</tr>)}
            <tr><td className="td font-medium">Features</td>{c.products.map((p) => <td key={p.id} className="td text-xs">{p.attributes.join(", ")}</td>)}</tr>
          </tbody></table></div>
        <div className="card mt-4"><p className="label">Comparison summary ({c.summary_method})</p><p className="whitespace-pre-wrap text-sm">{c.summary}</p></div>
      </>}
      <h2 className="mb-2 mt-8 text-lg font-semibold">Comparison history</h2>
      {history.data?.length ? <ul className="space-y-1 text-sm">{history.data.map((h) => <li key={h.id}><Link className="text-brand-600" to={`/app/compare?ids=${h.products.map((p) => p.id).join(",")}`}>{h.products.map((p) => p.name).join(" vs ")}</Link> <span className="text-xs text-slate-400">{new Date(h.created_at).toLocaleString()}</span></li>)}</ul> : <p className="text-sm text-slate-500">No comparisons yet.</p>}
    </>
  );
}
