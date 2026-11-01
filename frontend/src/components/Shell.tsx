import { Link, NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../lib/auth";
import { useCompareTray } from "../lib/compareTray";

const nav = [["/app", "Home"], ["/app/discover", "Discover"], ["/app/assistant", "AI Assistant"], ["/app/compare", "Compare"], ["/app/saved", "Saved"], ["/app/profile", "Profile"]];

export default function Shell() {
  const { logout } = useAuth();
  const tray = useCompareTray();
  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-10 border-b bg-white/90 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center gap-4 overflow-x-auto px-4 py-3">
          <Link to="/app" className="text-lg font-bold text-brand-600">ShopSense</Link>
          <nav className="flex gap-1">{nav.map(([to, label]) => <NavLink key={to} to={to} end className={({ isActive }) => `whitespace-nowrap rounded-lg px-3 py-1.5 text-sm ${isActive ? "bg-brand-50 font-medium text-brand-700" : "text-slate-600 hover:bg-slate-100"}`}>{label}</NavLink>)}</nav>
          <button className="ml-auto text-sm text-slate-500 hover:text-red-600" onClick={logout}>Sign out</button>
        </div>
        <div className="bg-amber-50 py-1 text-center text-xs text-amber-800">Demo catalog: products, brands and prices are sample data and not live retailer inventory.</div>
      </header>
      <main className="mx-auto max-w-7xl p-4 md:p-6"><Outlet /></main>
      {tray.ids.length > 0 && <div className="fixed bottom-4 right-4 flex items-center gap-3 rounded-full bg-slate-900 px-4 py-2 text-sm text-white shadow-lg">
        {tray.ids.length} selected <Link to="/app/compare" className="font-semibold text-emerald-300">Compare →</Link><button onClick={tray.clear} className="text-slate-400">✕</button></div>}
    </div>
  );
}
