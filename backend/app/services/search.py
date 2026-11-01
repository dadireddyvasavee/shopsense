from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core import llm
from app.models import Category, Product
from app.schemas import ParsedQuery

SORTS = {"price_asc": Product.price.asc(), "price_desc": Product.price.desc(), "name": Product.name.asc(),
         "newest": Product.created_at.desc()}


def keyword_search(db: Session, q: str | None = None, category: str | None = None, brands: list[str] | None = None,
                   min_price: float | None = None, max_price: float | None = None, sort: str = "relevance",
                   limit: int = 60) -> list[Product]:
    stmt = select(Product).join(Category)
    if q:
        for term in q.split():
            like = f"%{term}%"
            stmt = stmt.where(or_(Product.name.ilike(like), Product.brand.ilike(like), Product.description.ilike(like),
                                  Category.slug.ilike(like)))
    if category:
        stmt = stmt.where(Category.slug == category)
    if brands:
        stmt = stmt.where(Product.brand.in_(brands))
    if min_price is not None:
        stmt = stmt.where(Product.price >= min_price)
    if max_price is not None:
        stmt = stmt.where(Product.price <= max_price)
    stmt = stmt.order_by(SORTS.get(sort, Product.id.asc())).limit(limit)
    return list(db.scalars(stmt).unique().all())


def semantic_scores(products: list[Product], text: str) -> dict[int, float]:
    """Cosine similarity between the query and each product embedding (same embedder/dimension)."""
    if not products:
        return {}
    (qv,), _ = llm.embed([text])
    out = {}
    for p in products:
        q = qv if len(p.embedding) == len(qv) else llm._hash_embed(text, len(p.embedding))
        out[p.id] = llm.cosine(q, p.embedding)
    return out


def spec_ok(p: Product, req: dict) -> bool:
    for k, v in req.items():
        have = p.specifications.get(k)
        if isinstance(v, (int, float)) and isinstance(have, (int, float)):
            if have < v:
                return False
        elif have is not None and str(have).lower() != str(v).lower():
            return False
    return True


def constrained_candidates(db: Session, pq: ParsedQuery) -> list[Product]:
    items = keyword_search(db, category=pq.category, brands=pq.brands or None, min_price=pq.budget_min,
                           max_price=pq.budget_max, limit=500)
    return [p for p in items if spec_ok(p, pq.required_specs)]


def keyword_hits(p: Product, keywords: list[str]) -> list[str]:
    hay = " ".join([p.name, p.description, " ".join(p.attributes),
                    " ".join(f"{k} {v}" for k, v in p.specifications.items())]).lower()
    return [k for k in keywords if k in hay]
