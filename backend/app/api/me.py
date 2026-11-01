from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.core.db import get_db
from app.models import (AssistantTurn, BrowsingHistory, Product, ProductComparison, ProductInteraction, Recommendation,
                        SavedProduct, User, UserPreference)
from app.schemas import AssistantIn, AssistantOut, CompareIn, CompareOut, PreferencesIO, ProductOut, ScoredProduct
from app.services import assistant, recommender

router = APIRouter(prefix="/api", tags=["me"])


@router.get("/me/preferences", response_model=PreferencesIO)
def get_prefs(db: Session = Depends(get_db), user: User = Depends(current_user)):
    return db.scalar(select(UserPreference).where(UserPreference.user_id == user.id))


@router.put("/me/preferences", response_model=PreferencesIO)
def put_prefs(body: PreferencesIO, db: Session = Depends(get_db), user: User = Depends(current_user)):
    p = db.scalar(select(UserPreference).where(UserPreference.user_id == user.id))
    for k, v in body.model_dump().items():
        setattr(p, k, v)
    db.commit()
    return p


@router.get("/me/history", response_model=list[ProductOut])
def history(db: Session = Depends(get_db), user: User = Depends(current_user)):
    rows = db.execute(select(BrowsingHistory.product_id).where(BrowsingHistory.user_id == user.id)
                      .order_by(BrowsingHistory.id.desc()).limit(100)).scalars().all()
    seen, ordered = set(), []
    for pid in rows:
        if pid not in seen:
            seen.add(pid)
            ordered.append(pid)
    prods = {p.id: p for p in db.scalars(select(Product).where(Product.id.in_(ordered))).unique()}
    return [prods[i] for i in ordered[:20] if i in prods]


@router.get("/me/saved", response_model=list[ProductOut])
def saved(db: Session = Depends(get_db), user: User = Depends(current_user)):
    return [s.product for s in db.scalars(select(SavedProduct).where(SavedProduct.user_id == user.id)
                                          .order_by(SavedProduct.id.desc())).unique()]


@router.post("/me/saved/{pid}", status_code=201)
def save(pid: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    if not db.get(Product, pid):
        raise HTTPException(404, "Product not found")
    if not db.scalar(select(SavedProduct).where(SavedProduct.user_id == user.id, SavedProduct.product_id == pid)):
        db.add(SavedProduct(user_id=user.id, product_id=pid))
        db.add(ProductInteraction(user_id=user.id, product_id=pid, kind="save"))
        db.commit()
    return {"saved": True}


@router.delete("/me/saved/{pid}", status_code=204)
def unsave(pid: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    s = db.scalar(select(SavedProduct).where(SavedProduct.user_id == user.id, SavedProduct.product_id == pid))
    if s:
        db.delete(s)
        db.commit()


@router.get("/me/recommendations", response_model=list[ScoredProduct])
def recommendations(limit: int = 8, db: Session = Depends(get_db), user: User = Depends(current_user)):
    recs = recommender.recommend(db, user.id, limit)
    db.query(Recommendation).filter(Recommendation.user_id == user.id, Recommendation.context == "home",
                                    Recommendation.saved == 0).delete()
    rows = [Recommendation(user_id=user.id, product_id=p.id, score=s, reasons=r, context="home") for p, s, r in recs]
    db.add_all(rows)
    db.commit()
    return [ScoredProduct(product=p, score=s, reasons=r, rec_id=row.id) for (p, s, r), row in zip(recs, rows)]


@router.post("/me/recommendations/{rid}/save")
def save_rec(rid: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    r = db.get(Recommendation, rid)
    if not r or r.user_id != user.id:
        raise HTTPException(404, "Recommendation not found")
    r.saved = 1
    db.commit()
    return {"ok": True}


@router.get("/me/recommendations/saved")
def saved_recs(db: Session = Depends(get_db), user: User = Depends(current_user)):
    rows = db.scalars(select(Recommendation).where(Recommendation.user_id == user.id, Recommendation.saved == 1)
                      .order_by(Recommendation.id.desc())).unique()
    return [{"id": r.id, "score": r.score, "reasons": r.reasons, "context": r.context, "created_at": r.created_at,
             "product": ProductOut.model_validate(r.product)} for r in rows]


@router.post("/assistant", response_model=AssistantOut)
def chat(body: AssistantIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    pq, ranked = assistant.find(db, user.id, body.message)
    reply, method = assistant.explain(body.message, pq, ranked)
    db.add(AssistantTurn(user_id=user.id, query=body.message, parsed=pq.model_dump(), reply=reply,
                         product_ids=[p.id for p, _, _ in ranked]))
    rows = [Recommendation(user_id=user.id, product_id=p.id, score=s, reasons=r, context="assistant")
            for p, s, r in ranked]
    db.add_all(rows)
    db.commit()
    return AssistantOut(reply=reply, reply_method=method, parsed=pq,
                        results=[ScoredProduct(product=p, score=s, reasons=r, rec_id=row.id)
                                 for (p, s, r), row in zip(ranked, rows)])


@router.get("/assistant/history")
def assistant_history(db: Session = Depends(get_db), user: User = Depends(current_user)):
    rows = db.scalars(select(AssistantTurn).where(AssistantTurn.user_id == user.id)
                      .order_by(AssistantTurn.id.desc()).limit(20)).all()
    return [{"id": t.id, "query": t.query, "reply": t.reply, "created_at": t.created_at} for t in rows]


def _cmp_out(c: ProductComparison, db: Session) -> CompareOut:
    prods = {p.id: p for p in db.scalars(select(Product).where(Product.id.in_(c.product_ids))).unique()}
    ordered = [prods[i] for i in c.product_ids if i in prods]
    keys = sorted({k for p in ordered for k in p.specifications})
    return CompareOut(id=c.id, products=ordered, spec_keys=keys, summary=c.summary, summary_method=c.summary_method,
                      created_at=c.created_at)


@router.post("/compare", response_model=CompareOut, status_code=201)
def compare(body: CompareIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    ids = list(dict.fromkeys(body.product_ids))
    prods = list(db.scalars(select(Product).where(Product.id.in_(ids))).unique())
    if len(prods) != len(ids) or len(ids) < 2:
        raise HTTPException(422, "Provide 2–4 distinct, existing product ids")
    prods.sort(key=lambda p: ids.index(p.id))
    summary, method = assistant.compare_summary(prods)
    c = ProductComparison(user_id=user.id, product_ids=ids, summary=summary, summary_method=method)
    db.add(c)
    for p in prods:
        db.add(ProductInteraction(user_id=user.id, product_id=p.id, kind="compare"))
    db.commit()
    db.refresh(c)
    return _cmp_out(c, db)


@router.get("/compare/history", response_model=list[CompareOut])
def compare_history(db: Session = Depends(get_db), user: User = Depends(current_user)):
    rows = db.scalars(select(ProductComparison).where(ProductComparison.user_id == user.id)
                      .order_by(ProductComparison.id.desc()).limit(20)).all()
    return [_cmp_out(c, db) for c in rows]
