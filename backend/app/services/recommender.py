"""Hybrid recommender: content-based similarity to the user's interaction profile + preference-based ranking.

score = 0.40 * content_similarity      (cosine between product and weighted profile vector)
      + 0.20 * category_affinity       (explicit favourite categories + interaction share)
      + 0.15 * brand_affinity          (explicit favourite brands + interaction share)
      + 0.15 * budget_fit              (1 inside budget, decays above it)
      + 0.10 * interest_match          (overlap of explicit interests with product attributes)
Disliked products are excluded. Every component that contributes is reported as a reason.
"""
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import llm
from app.models import Product, ProductInteraction, UserPreference

WEIGHTS = {"view": 1.0, "compare": 1.5, "save": 3.0, "like": 3.0, "dislike": -3.0}


class Profile:
    def __init__(self, db: Session, user_id: int):
        self.pref = db.scalar(select(UserPreference).where(UserPreference.user_id == user_id)) or UserPreference()
        inter = db.scalars(select(ProductInteraction).where(ProductInteraction.user_id == user_id)).all()
        products = {p.id: p for p in db.scalars(select(Product).where(
            Product.id.in_({i.product_id for i in inter}))).unique().all()} if inter else {}
        self.weight: dict[int, float] = defaultdict(float)
        for i in inter:
            self.weight[i.product_id] += WEIGHTS.get(i.kind, 0) * i.weight
        self.disliked = {pid for pid, w in self.weight.items() if w < 0}
        pos = {pid: w for pid, w in self.weight.items() if w > 0 and pid in products}
        self.cat_aff: dict[str, float] = defaultdict(float)
        self.brand_aff: dict[str, float] = defaultdict(float)
        total = sum(pos.values()) or 1.0
        self.vector: list[float] | None = None
        for pid, w in pos.items():
            p = products[pid]
            self.cat_aff[p.category.slug] += w / total
            self.brand_aff[p.brand] += w / total
            if p.embedding:
                if self.vector is None:
                    self.vector = [0.0] * len(p.embedding)
                if len(p.embedding) == len(self.vector):
                    self.vector = [a + w * b for a, b in zip(self.vector, p.embedding)]
        self.seen = set(pos)
        self.has_signal = bool(pos) or bool(self.pref.favorite_categories or self.pref.favorite_brands
                                            or self.pref.interests or self.pref.budget_max)


def score_product(p: Product, prof: Profile) -> tuple[float, list[str]]:
    reasons: list[str] = []
    pref = prof.pref
    content = max(0.0, llm.cosine(prof.vector, p.embedding)) if prof.vector and p.embedding else 0.0
    if content > 0.25:
        reasons.append("Similar to products you viewed, saved or liked")
    cat = (1.0 if p.category.slug in (pref.favorite_categories or []) else 0.0)
    cat = max(cat, min(1.0, prof.cat_aff.get(p.category.slug, 0) * 2))
    if p.category.slug in (pref.favorite_categories or []):
        reasons.append(f"In your favourite category: {p.category.name}")
    elif prof.cat_aff.get(p.category.slug, 0) > 0.2:
        reasons.append(f"You often browse {p.category.name}")
    brand = 1.0 if p.brand in (pref.favorite_brands or []) else min(1.0, prof.brand_aff.get(p.brand, 0) * 2)
    if p.brand in (pref.favorite_brands or []):
        reasons.append(f"From your favourite brand {p.brand}")
    if pref.budget_max:
        budget = 1.0 if p.price <= pref.budget_max else max(0.0, 1 - (p.price - pref.budget_max) / pref.budget_max)
        if p.price <= pref.budget_max:
            reasons.append(f"Within your budget of ₹{pref.budget_max:,.0f}")
    else:
        budget = 0.5
    attrs = {a.lower() for a in p.attributes}
    hits = [i for i in (pref.interests or []) if i.lower() in attrs]
    interest = min(1.0, len(hits) / 2)
    if hits:
        reasons.append("Matches your interests: " + ", ".join(hits))
    s = 0.40 * content + 0.20 * cat + 0.15 * brand + 0.15 * budget + 0.10 * interest
    return round(s, 4), reasons


def recommend(db: Session, user_id: int, limit: int = 8, candidates: list[Product] | None = None,
              exclude_seen: bool = True) -> list[tuple[Product, float, list[str]]]:
    prof = Profile(db, user_id)
    pool = candidates if candidates is not None else list(db.scalars(select(Product)).unique().all())
    out = []
    for p in pool:
        if p.id in prof.disliked or (exclude_seen and p.id in prof.seen and candidates is None):
            continue
        s, r = score_product(p, prof)
        out.append((p, s, r or ["Not personalised yet — browse, save or set preferences to improve this"]))
    out.sort(key=lambda x: (-x[1], x[0].price))
    return out[:limit]
