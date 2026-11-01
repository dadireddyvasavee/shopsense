"""Catalog ingestion. Accepts a list of product dicts (JSON file or API upload) and upserts by SKU."""
import json
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core import llm
from app.models import Category, Product

DEMO_FILE = Path(__file__).resolve().parents[2] / "data" / "demo_catalog.json"
REQUIRED = {"sku", "name", "category", "brand", "price", "description"}


def product_text(p: dict | Product) -> str:
    g = (lambda k: p[k]) if isinstance(p, dict) else (lambda k: getattr(p, k))
    cat = g("category") if isinstance(p, dict) else p.category.slug
    specs = " ".join(f"{k} {v}" for k, v in (g("specifications") or {}).items())
    return f"{g('name')} {g('brand')} {cat} {g('description')} {' '.join(g('attributes') or [])} {specs}"


def ingest(db: Session, items: list[dict], source: str = "demo") -> dict:
    created = updated = 0
    errors: list[str] = []
    valid = []
    for i, it in enumerate(items):
        missing = REQUIRED - it.keys()
        if missing:
            errors.append(f"item {i}: missing {sorted(missing)}")
        elif not isinstance(it["price"], (int, float)) or it["price"] <= 0:
            errors.append(f"item {i}: invalid price")
        else:
            valid.append(it)
    vectors, _ = llm.embed([product_text(it) for it in valid]) if valid else ([], "")
    cats = {c.slug: c for c in db.scalars(select(Category)).all()}
    for it, vec in zip(valid, vectors):
        slug = it["category"].strip().lower()
        if slug not in cats:
            cats[slug] = Category(slug=slug, name=slug.replace("-", " ").title())
            db.add(cats[slug])
            db.flush()
        p = db.scalar(select(Product).where(Product.sku == it["sku"]))
        fields = dict(name=it["name"], brand=it["brand"], description=it["description"], price=float(it["price"]),
                      specifications=it.get("specifications", {}), attributes=it.get("attributes", []),
                      image_url=it.get("image_url"), source=source, embedding=vec, category_id=cats[slug].id)
        if p:
            for k, v in fields.items():
                setattr(p, k, v)
            updated += 1
        else:
            db.add(Product(sku=it["sku"], **fields))
            created += 1
    db.commit()
    return {"created": created, "updated": updated, "errors": errors}


def seed_demo_if_empty(db: Session) -> None:
    if db.scalar(select(func.count()).select_from(Product)) == 0 and DEMO_FILE.exists():
        ingest(db, json.loads(DEMO_FILE.read_text()), source="demo")
