# ShopSense — AI-Powered Personalized Shopping & Product Discovery

ShopSense is a consumer shopping app where you describe what you need ("a laptop under ₹70,000 for programming") and get **catalog-grounded recommendations with reasons**, plus keyword/semantic search, a hybrid personalized recommender, product comparison, saved items and browsing history.

> ⚠️ **Demo catalog.** `backend/data/demo_catalog.json` has 34 products from **fictional brands** (Nimbus, Voltra, Stride, Dewleaf…) in 5 categories. They aren't real retailer listings. Nothing is scraped, and the UI says so on every page. Plug in a real feed with `python -m app.cli ingest your_feed.json`.

**Stack:** React 18 + TypeScript + Vite + Tailwind + React Router · FastAPI + SQLAlchemy 2 + Pydantic 2 + Alembic · PostgreSQL · OpenAI-compatible LLM + embeddings · Docker · GitHub Actions · Pytest/Vitest.
Architecture diagram and ranking formulas: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Features
| Area | What works |
|---|---|
| Conversational assistant | Extracts category, budget/range, brands, specs, keywords → filters real catalog → ranks → explains each pick. Shows how the request was understood. Says plainly when nothing matches. |
| Discovery | Keyword search, natural-language/semantic search, category/brand/price filters, sorting, similar products |
| Recommendations | Hybrid content-based + preference ranking with interpretable reasons; like/dislike feedback; save recommendations |
| Profile | Budget, favourite categories/brands, interests, browsing history, saved products, recent assistant searches |
| Comparison | 2–4 products side by side (price vs your budget, all specs, features) + summary (LLM from catalog JSON, or deterministic) + history |
| Dashboard | Recommendations, recently viewed, saved, popular categories, quick assistant, comparison history |

## Run with Docker
```bash
cp backend/.env.example backend/.env    # optional: add LLM_API_KEY
docker compose up --build
```
App → http://localhost:8080 · Swagger → http://localhost:8000/docs. The demo catalog is loaded automatically on first start (`SEED_DEMO=true`).

## Run locally
```bash
cd backend && python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
cp .env.example .env && alembic upgrade head && python -m app.cli seed && uvicorn app.main:app --reload
cd ../frontend && npm install && npm run dev        # http://localhost:5173
```
Optional admin: `python -m app.cli make-admin you@example.com` enables `POST /api/catalog/ingest`.

## Without an LLM key
Everything still works. Query understanding uses the rules parser, explanations use deterministic templates, comparisons use the rule-based summary, and embeddings use the local hashing embedder. Responses report which method was used (`parsed.method`, `reply_method`, `summary_method`).

## Tests
```bash
cd backend && pytest -q     # 10 tests: parser, filters/sort, assistant constraints, LLM-output validation,
                            # personalization, saved/history, dislike exclusion, comparison, admin guard
cd frontend && npm test
```

## Deployment
Same as any FastAPI + static SPA: container for `backend/` (runs migrations on boot) with a managed PostgreSQL, and `frontend/` as a static site (`VITE_API_URL=https://your-api`). Render, Railway, Fly.io and Azure Container Apps all work.

## Known limitations
- Semantic retrieval is brute-force cosine over JSON vectors. That's fine for thousands of products; move to pgvector at scale.
- Without an LLM, the parser is rules-based and supports the categories in `SYNONYMS` (extend it in `app/services/query.py`).
- No real product images (no licensed images exist for fictional products). Category tiles are rendered instead.
- No checkout or stock: out of scope, and stock is deliberately never claimed.
- No screenshots are bundled. Capture them from your running instance.
