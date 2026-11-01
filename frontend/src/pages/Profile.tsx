import { FormEvent, useEffect, useState } from "react";
import { ErrorBox, PageHeader, Spinner } from "../components/ui";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { useApi } from "../lib/useApi";
import { Category, Prefs } from "../types";

export default function Profile() {
  const { user } = useAuth();
  const prefs = useApi<Prefs>("/api/me/preferences");
  const cats = useApi<Category[]>("/api/categories");
  const brands = useApi<string[]>("/api/brands");
  const history = useApi<{ id: number; query: string; created_at: string }[]>("/api/assistant/history");
  const [f, setF] = useState<Prefs | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  useEffect(() => { if (prefs.data) setF(prefs.data); }, [prefs.data]);
  if (!f) return prefs.error ? <ErrorBox msg={prefs.error} /> : <Spinner />;
  const toggle = (k: "favorite_categories" | "favorite_brands", v: string) => setF({ ...f, [k]: f[k].includes(v) ? f[k].filter((x) => x !== v) : [...f[k], v] });
  const save = async (e: FormEvent) => { e.preventDefault(); try { await api("/api/me/preferences", { method: "PUT", json: f }); setMsg("Preferences saved. Recommendations updated."); } catch (x) { setMsg((x as Error).message); } };
  return (
    <>
      <PageHeader title="Your profile" />
      <div className="grid gap-6 lg:grid-cols-3">
        <form onSubmit={save} className="card space-y-5 lg:col-span-2">
          <p className="text-sm text-slate-600">{user?.full_name} · {user?.email}</p>
          <label className="block"><span className="label">Default budget (₹, max)</span><input className="input max-w-xs" type="number" min={0} value={f.budget_max ?? ""} onChange={(e) => setF({ ...f, budget_max: e.target.value ? Number(e.target.value) : null })} /></label>
          <div><p className="label">Favourite categories</p><div className="flex flex-wrap gap-2">{cats.data?.map((c) => <button type="button" key={c.slug} onClick={() => toggle("favorite_categories", c.slug)} className={`rounded-full border px-3 py-1 text-sm ${f.favorite_categories.includes(c.slug) ? "border-brand-600 bg-brand-50 text-brand-700" : ""}`}>{c.name}</button>)}</div></div>
          <div><p className="label">Favourite brands</p><div className="flex flex-wrap gap-2">{brands.data?.map((b) => <button type="button" key={b} onClick={() => toggle("favorite_brands", b)} className={`rounded-full border px-3 py-1 text-sm ${f.favorite_brands.includes(b) ? "border-brand-600 bg-brand-50 text-brand-700" : ""}`}>{b}</button>)}</div></div>
          <label className="block"><span className="label">Interests (comma separated, e.g. programming, walking, oily skin)</span><input className="input" value={f.interests.join(", ")} onChange={(e) => setF({ ...f, interests: e.target.value.split(",").map((s) => s.trim()).filter(Boolean) })} /></label>
          <button className="btn">Save preferences</button>{msg && <span className="ml-3 text-sm text-slate-500">{msg}</span>}
        </form>
        <div className="card"><p className="label">Recent assistant searches</p><ul className="space-y-2 text-sm">{history.data?.map((h) => <li key={h.id}>{h.query}<p className="text-xs text-slate-400">{new Date(h.created_at).toLocaleString()}</p></li>)}</ul></div>
      </div>
    </>
  );
}
