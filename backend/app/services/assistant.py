"""Conversational shopping: understand -> retrieve from catalog -> rank -> explain (LLM only rephrases catalog facts)."""
import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import llm
from app.models import Category, Product
from app.schemas import ParsedQuery
from app.services import query, recommender, search


def catalog_vocab(db: Session) -> tuple[list[str], list[str]]:
    cats = list(db.scalars(select(Category.slug)).all())
    brands = sorted(set(db.scalars(select(Product.brand)).all()))
    return cats, brands


def find(db: Session, user_id: int, text: str, limit: int = 5) -> tuple[ParsedQuery, list[tuple[Product, float, list[str]]]]:
    cats, brands = catalog_vocab(db)
    pq = query.understand(text, cats, brands)
    cands = search.constrained_candidates(db, pq)
    sem = search.semantic_scores(cands, " ".join([text] + pq.keywords))
    personal = {p.id: (s, r) for p, s, r in recommender.recommend(db, user_id, limit=10_000, candidates=cands)}
    ranked = []
    for p in cands:
        hits = search.keyword_hits(p, pq.keywords)
        ps, preasons = personal.get(p.id, (0.0, []))
        score = 0.5 * sem.get(p.id, 0) + 0.3 * (len(hits) / max(1, len(pq.keywords))) + 0.2 * ps
        reasons = []
        if pq.budget_max:
            reasons.append(f"₹{p.price:,.0f} is within your ₹{pq.budget_max:,.0f} budget")
        if pq.category:
            reasons.append(f"Category: {p.category.name}")
        if hits:
            reasons.append("Matches: " + ", ".join(hits))
        for k, v in pq.required_specs.items():
            reasons.append(f"{k} = {p.specifications.get(k)} (needed {v})")
        reasons += [r for r in preasons if "budget" not in r and not r.startswith("Not personalised")]
        ranked.append((p, round(score, 4), reasons))
    ranked.sort(key=lambda x: (-x[1], x[0].price))
    return pq, ranked[:limit]


def facts(p: Product) -> dict:
    return {"id": p.id, "name": p.name, "brand": p.brand, "category": p.category.slug, "price_inr": p.price,
            "specifications": p.specifications, "attributes": p.attributes, "description": p.description}


def template_reply(pq: ParsedQuery, ranked) -> str:
    if not ranked:
        bits = [f"category '{pq.category}'" if pq.category else None,
                f"budget ₹{pq.budget_max:,.0f}" if pq.budget_max else None]
        return ("I couldn't find products in our demo catalog matching " + (", ".join(b for b in bits if b) or "that request")
                + ". Try raising the budget or removing a filter.")
    lines = [f"Here are {len(ranked)} options from our demo catalog:"]
    for p, _, r in ranked:
        lines.append(f"• {p.name} ({p.brand}) – ₹{p.price:,.0f}: " + "; ".join(r[:3]))
    return "\n".join(lines)


def explain(text: str, pq: ParsedQuery, ranked) -> tuple[str, str]:
    if not ranked or not llm.llm_configured():
        return template_reply(pq, ranked), "template"
    try:
        out = llm.chat([
            {"role": "system", "content": (
                "You are a shopping assistant. Recommend ONLY from the products given in JSON, in the given order. "
                "Use only the facts provided (price, specifications, attributes). Never invent specs, prices, stock, "
                "reviews or ratings. For each product explain in one or two sentences why it fits the request. "
                "Mention that prices come from a demo catalog.")},
            {"role": "user", "content": f"Request: {text}\nParsed: {pq.model_dump_json()}\nProducts: "
                                        f"{json.dumps([facts(p) for p, _, _ in ranked])}"}])
        return out, "llm"
    except llm.LLMUnavailable:
        return template_reply(pq, ranked), "template"


def compare_summary(products: list[Product]) -> tuple[str, str]:
    det = deterministic_comparison(products)
    if not llm.llm_configured():
        return det, "deterministic"
    try:
        return llm.chat([
            {"role": "system", "content": "Compare these products strictly using the JSON facts. No invented data. "
                                          "Give a short verdict per use-case (budget, performance, portability, etc.) "
                                          "only where the data supports it."},
            {"role": "user", "content": json.dumps([facts(p) for p in products])}]), "llm"
    except llm.LLMUnavailable:
        return det, "deterministic"


def deterministic_comparison(products: list[Product]) -> str:
    lines = []
    cheapest = min(products, key=lambda p: p.price)
    lines.append(f"Lowest price: {cheapest.name} at ₹{cheapest.price:,.0f}.")
    keys = sorted({k for p in products for k, v in p.specifications.items() if isinstance(v, (int, float))
                   and not isinstance(v, bool)})
    lower_better = {"weight_kg", "weight_g"}
    for k in keys:
        vals = [(p, p.specifications[k]) for p in products if isinstance(p.specifications.get(k), (int, float))]
        if len(vals) < 2 or len({v for _, v in vals}) == 1:
            continue
        best = (min if k in lower_better else max)(vals, key=lambda x: x[1])
        lines.append(f"{'Lowest' if k in lower_better else 'Highest'} {k.replace('_', ' ')}: {best[0].name} ({best[1]}).")
    cats = {p.category.slug for p in products}
    if len(cats) > 1:
        lines.append("Note: these products are from different categories: " + ", ".join(sorted(cats)) + ".")
    return " ".join(lines)
