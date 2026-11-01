import { FormEvent, useEffect, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { ProductCard } from "../components/ProductCard";
import { Badge, ErrorBox } from "../components/ui";
import { api } from "../lib/api";
import { AssistantOut } from "../types";

type Turn = { q: string; a?: AssistantOut; err?: string };
const EXAMPLES = ["Find a laptop under ₹70,000 for programming", "Recommend comfortable shoes for daily walking", "Find skincare products suitable for a simple routine", "Compare Voltra phones under 20k"];

export default function Assistant() {
  const [sp] = useSearchParams();
  const [turns, setTurns] = useState<Turn[]>([]);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [saved, setSaved] = useState<Set<number>>(new Set());
  const end = useRef<HTMLDivElement>(null);
  const ask = async (q: string) => {
    setBusy(true); setTurns((t) => [...t, { q }]); setText("");
    try { const a = await api<AssistantOut>("/api/assistant", { method: "POST", json: { message: q } }); setTurns((t) => [...t.slice(0, -1), { q, a }]); }
    catch (e) { setTurns((t) => [...t.slice(0, -1), { q, err: (e as Error).message }]); } finally { setBusy(false); }
  };
  useEffect(() => { const q = sp.get("q"); if (q) ask(q); }, []); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => end.current?.scrollIntoView({ behavior: "smooth" }), [turns]);
  const saveRec = async (rid: number) => { await api(`/api/me/recommendations/${rid}/save`, { method: "POST" }); setSaved(new Set(saved).add(rid)); };
  const submit = (e: FormEvent) => { e.preventDefault(); if (text.trim()) ask(text); };
  return (
    <div className="mx-auto max-w-5xl">
      <h1 className="mb-4 text-2xl font-semibold">AI shopping assistant</h1>
      {!turns.length && <div className="mb-6 flex flex-wrap gap-2">{EXAMPLES.map((e) => <button key={e} onClick={() => ask(e)} className="rounded-full border bg-white px-4 py-2 text-sm hover:border-brand-500">{e}</button>)}</div>}
      <div className="space-y-6">{turns.map((t, i) => (
        <div key={i} className="space-y-3">
          <div className="flex justify-end"><div className="rounded-2xl bg-brand-600 px-4 py-2 text-white">{t.q}</div></div>
          {t.err && <ErrorBox msg={t.err} />}
          {t.a && <div className="card space-y-4">
            <div className="flex flex-wrap gap-1 text-xs">Understood as: {t.a.parsed.category && <Badge tone="brand">{t.a.parsed.category}</Badge>}
              {t.a.parsed.budget_max && <Badge tone="brand">≤ ₹{t.a.parsed.budget_max.toLocaleString("en-IN")}</Badge>}
              {t.a.parsed.budget_min && <Badge tone="brand">≥ ₹{t.a.parsed.budget_min.toLocaleString("en-IN")}</Badge>}
              {t.a.parsed.brands.map((b) => <Badge key={b}>{b}</Badge>)}{t.a.parsed.keywords.map((k) => <Badge key={k}>{k}</Badge>)}
              <span className="text-slate-400">· parser: {t.a.parsed.method} · reply: {t.a.reply_method}</span></div>
            <p className="whitespace-pre-wrap text-sm text-slate-800">{t.a.reply}</p>
            <div className="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-5">{t.a.results.map((r) => <div key={r.product.id}><ProductCard p={r.product} reasons={r.reasons} score={r.score} />
              {r.rec_id && <button disabled={saved.has(r.rec_id)} onClick={() => saveRec(r.rec_id!)} className="mt-1 w-full text-xs text-brand-600 disabled:text-slate-400">{saved.has(r.rec_id) ? "Recommendation saved" : "Save recommendation"}</button>}</div>)}</div>
          </div>}
        </div>))}
        {busy && <p className="text-sm text-slate-400">Searching the catalog…</p>}<div ref={end} /></div>
      <form onSubmit={submit} className="sticky bottom-4 mt-6 flex gap-2 rounded-xl border bg-white p-2 shadow"><input className="input border-0" value={text} onChange={(e) => setText(e.target.value)} placeholder="Describe what you want, budget and must-haves…" /><button className="btn" disabled={busy}>Ask</button></form>
    </div>
  );
}
