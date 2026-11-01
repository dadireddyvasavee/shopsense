from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.core.db import get_db
from app.models import BrowsingHistory, Category, Product, ProductInteraction, User
from app.schemas import CategoryOut, InteractionIn, ProductOut, ScoredProduct
from app.services import assistant, catalog, search

router = APIRouter(prefix="/api", tags=["catalog"])


@router.get("/categories", response_model=list[CategoryOut])
def categories(db: Session = Depends(get_db)):
    return db.scalars(select(Category).order_by(Category.name)).all()


@router.get("/brands", response_model=list[str])
def brands(category: str | None = None, db: Session = Depends(get_db)):
    stmt = select(Product.brand).distinct()
    if category:
        stmt = stmt.join(Category).where(Category.slug == category)
    return sorted(db.scalars(stmt).all())


@router.get("/products", response_model=list[ProductOut])
def list_products(q: str | None = None, category: str | None = None, brand: list[str] | None = Query(None),
                  min_price: float | None = Query(None, ge=0), max_price: float | None = Query(None, ge=0),
                  sort: str = Query("relevance", pattern="^(relevance|price_asc|price_desc|name|newest)$"),
                  db: Session = Depends(get_db)):
    """Keyword search + category/brand/price filters + sorting."""
    return search.keyword_search(db, q, category, brand, min_price, max_price, sort)


@router.get("/products/semantic", response_model=list[ScoredProduct])
def semantic(q: str = Query(min_length=2), limit: int = Query(10, le=50), db: Session = Depends(get_db),
             user: User = Depends(current_user)):
    """Natural-language search: parse constraints, filter catalog, rank by semantic similarity + preferences."""
    _, ranked = assistant.find(db, user.id, q, limit)
    return [ScoredProduct(product=p, score=s, reasons=r) for p, s, r in ranked]


@router.get("/products/{pid}", response_model=ProductOut)
def product(pid: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    p = db.get(Product, pid)
    if not p:
        raise HTTPException(404, "Product not found")
    db.add(BrowsingHistory(user_id=user.id, product_id=pid))
    db.add(ProductInteraction(user_id=user.id, product_id=pid, kind="view"))
    db.commit()
    return p


@router.get("/products/{pid}/similar", response_model=list[ProductOut])
def similar(pid: int, db: Session = Depends(get_db)):
    p = db.get(Product, pid)
    if not p:
        raise HTTPException(404, "Product not found")
    others = [o for o in db.scalars(select(Product).where(Product.category_id == p.category_id, Product.id != pid)).unique()]
    from app.core.llm import cosine
    return sorted(others, key=lambda o: -cosine(o.embedding, p.embedding))[:4]


@router.post("/products/{pid}/feedback", status_code=201)
def feedback(pid: int, body: InteractionIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    if not db.get(Product, pid):
        raise HTTPException(404, "Product not found")
    db.add(ProductInteraction(user_id=user.id, product_id=pid, kind=body.kind))
    db.commit()
    return {"ok": True}


@router.post("/catalog/ingest", tags=["admin"])
def ingest(items: list[dict], db: Session = Depends(get_db), user: User = Depends(current_user)):
    """Extensible ingestion: POST a JSON array of products (sku, name, category, brand, price, description, ...)."""
    if user.role != "admin":
        raise HTTPException(403, "Admin only")
    return catalog.ingest(db, items, source="admin-upload")


@router.get("/stats/popular-categories")
def popular_categories(db: Session = Depends(get_db)):
    rows = db.execute(select(Category.slug, Category.name, func.count(ProductInteraction.id))
                      .select_from(Category).join(Product).outerjoin(ProductInteraction)
                      .group_by(Category.id).order_by(func.count(ProductInteraction.id).desc())).all()
    return [{"slug": s, "name": n, "interactions": c} for s, n, c in rows]
