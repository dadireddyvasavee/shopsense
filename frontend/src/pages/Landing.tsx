import { Link } from "react-router-dom";

export default function Landing() {
  const ex = ["Find a laptop under ₹70,000 for programming", "Recommend comfortable shoes for daily walking", "Skincare for a simple routine"];
  return (
    <div className="min-h-screen bg-gradient-to-b from-brand-50 to-white">
      <header className="mx-auto flex max-w-6xl items-center justify-between p-6"><span className="text-xl font-bold text-brand-600">ShopSense</span>
        <div className="flex gap-2"><Link to="/login" className="btn-ghost">Sign in</Link><Link to="/register" className="btn">Start shopping</Link></div></header>
      <section className="mx-auto max-w-3xl px-6 py-20 text-center">
        <h1 className="text-4xl font-bold tracking-tight md:text-5xl">Tell us what you need. We'll find what fits.</h1>
        <p className="mt-5 text-lg text-slate-600">An AI shopping assistant that understands budgets, use cases and specs, then recommends from real catalog data and explains every pick.</p>
        <div className="mt-8 flex flex-wrap justify-center gap-2">{ex.map((e) => <span key={e} className="rounded-full border border-brand-100 bg-white px-4 py-2 text-sm text-slate-700">“{e}”</span>)}</div>
        <Link to="/register" className="btn mt-8 px-6 py-3 text-base">Create free account</Link>
      </section>
    </div>
  );
}
