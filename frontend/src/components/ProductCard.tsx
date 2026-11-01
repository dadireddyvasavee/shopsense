import { Link } from "react-router-dom";
import { useCompareTray } from "../lib/compareTray";
import { Product } from "../types";

const ICON: Record<string, string> = { laptops: "💻", shoes: "👟", skincare: "🧴", smartphones: "📱", audio: "🎧" };
export const inr = (n: number) => `₹${n.toLocaleString("en-IN")}`;

export function ProductImage({ p, big = false }: { p: Product; big?: boolean }) {
  if (p.image_url) return <img src={p.image_url} alt={p.name} className={`w-full rounded-lg object-cover ${big ? "h-72" : "h-36"}`} />;
  return <div className={`flex w-full items-center justify-center rounded-lg bg-gradient-to-br from-brand-50 to-slate-100 ${big ? "h-72 text-7xl" : "h-36 text-5xl"}`} aria-label={p.name}>{ICON[p.category.slug] ?? "🛍️"}</div>;
}

export function ProductCard({ p, reasons, score }: { p: Product; reasons?: string[]; score?: number }) {
  const tray = useCompareTray();
  return (
    <div className="card flex flex-col p-3">
      <Link to={`/app/products/${p.id}`}><ProductImage p={p} /></Link>
      <div className="mt-3 flex-1">
        <p className="text-xs text-slate-500">{p.brand} · {p.category.name}</p>
        <Link to={`/app/products/${p.id}`} className="font-medium text-slate-900 hover:text-brand-600">{p.name}</Link>
        <p className="mt-1 font-semibold">{inr(p.price)}</p>
        {reasons && reasons.length > 0 && <ul className="mt-2 space-y-0.5 text-xs text-emerald-700">{reasons.slice(0, 3).map((r) => <li key={r}>✓ {r}</li>)}</ul>}
        {score !== undefined && <p className="mt-1 text-[10px] text-slate-400">match score {score.toFixed(2)}</p>}
      </div>
      <label className="mt-3 flex items-center gap-2 text-xs text-slate-600"><input type="checkbox" checked={tray.ids.includes(p.id)} onChange={() => tray.toggle(p.id)} /> Compare</label>
    </div>
  );
}
