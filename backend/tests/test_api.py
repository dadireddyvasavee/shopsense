def _ids(client, auth, **params):
    return [p["id"] for p in client.get("/api/products", params=params, headers=auth).json()]


def test_catalog_filters_and_sort(client, auth):
    lap = client.get("/api/products", params={"category": "laptops", "max_price": 70000, "sort": "price_asc"}).json()
    assert lap and all(p["category"]["slug"] == "laptops" and p["price"] <= 70000 for p in lap)
    assert [p["price"] for p in lap] == sorted(p["price"] for p in lap)
    assert all(p["source"] == "demo" for p in lap)
    assert all(p["brand"] == "Stride" for p in client.get("/api/products", params={"brand": "Stride"}).json())
    assert client.get("/api/products", params={"q": "sunscreen"}).json()[0]["category"]["slug"] == "skincare"


def test_assistant_respects_constraints_without_llm(client, auth):
    r = client.post("/api/assistant", headers=auth, json={"message": "Find a laptop under ₹70,000 for programming"}).json()
    assert r["parsed"]["category"] == "laptops" and r["parsed"]["budget_max"] == 70000
    assert r["results"] and all(x["product"]["price"] <= 70000 and x["product"]["category"]["slug"] == "laptops" for x in r["results"])
    top = r["results"][0]
    assert "programming" in top["product"]["attributes"]
    assert r["reply_method"] == "template" and top["product"]["name"] in r["reply"]
    assert any("budget" in reason for reason in top["reasons"])


def test_assistant_no_match_is_honest(client, auth):
    r = client.post("/api/assistant", headers=auth, json={"message": "laptop under 5000"}).json()
    assert r["results"] == [] and "couldn't find" in r["reply"]


def test_llm_explanation_uses_catalog_facts(client, auth, monkeypatch):
    from app.core import llm
    seen = {}
    monkeypatch.setattr(llm, "llm_configured", lambda: True)
    monkeypatch.setattr(llm, "chat_json", lambda m: {"category": "shoes", "budget_max": 4000, "brands": ["FakeBrand"], "keywords": ["walking"]})
    def fake_chat(messages, **k):
        seen["payload"] = messages[-1]["content"]
        return "LLM explanation"
    monkeypatch.setattr(llm, "chat", fake_chat)
    r = client.post("/api/assistant", headers=auth, json={"message": "comfortable walking shoes"}).json()
    assert r["parsed"]["brands"] == []  # hallucinated brand rejected by validation
    assert r["parsed"]["method"] == "llm+validated" and r["reply"] == "LLM explanation"
    assert all(x["product"]["price"] <= 4000 for x in r["results"])
    assert r["results"][0]["product"]["name"] in seen["payload"]


def test_personalization_and_saved(client, auth):
    client.put("/api/me/preferences", headers=auth, json={"budget_max": 3000, "favorite_categories": ["shoes"],
                                                          "favorite_brands": ["Pacelyn"], "interests": ["walking"]})
    recs = client.get("/api/me/recommendations", headers=auth).json()
    assert recs[0]["product"]["category"]["slug"] == "shoes" and recs[0]["reasons"]
    rid = recs[0]["rec_id"]
    assert client.post(f"/api/me/recommendations/{rid}/save", headers=auth).status_code == 200
    assert client.get("/api/me/recommendations/saved", headers=auth).json()[0]["id"] == rid
    pid = recs[0]["product"]["id"]
    client.get(f"/api/products/{pid}", headers=auth)
    assert client.get("/api/me/history", headers=auth).json()[0]["id"] == pid
    client.post(f"/api/me/saved/{pid}", headers=auth)
    client.post(f"/api/me/saved/{pid}", headers=auth)  # idempotent
    assert [p["id"] for p in client.get("/api/me/saved", headers=auth).json()] == [pid]
    client.post(f"/api/products/{pid}/feedback", headers=auth, json={"kind": "dislike"})
    client.post(f"/api/products/{pid}/feedback", headers=auth, json={"kind": "dislike"})
    assert pid not in [r["product"]["id"] for r in client.get("/api/me/recommendations?limit=50", headers=auth).json()]


def test_compare_and_history(client, auth):
    ids = _ids(client, auth, category="laptops")[:3]
    r = client.post("/api/compare", headers=auth, json={"product_ids": ids})
    assert r.status_code == 201
    body = r.json()
    assert body["summary_method"] == "deterministic" and "Lowest price" in body["summary"] and "ram_gb" in body["spec_keys"]
    assert client.get("/api/compare/history", headers=auth).json()[0]["id"] == body["id"]
    assert client.post("/api/compare", headers=auth, json={"product_ids": [ids[0], 99999]}).status_code == 422


def test_ingest_requires_admin(client, auth):
    assert client.post("/api/catalog/ingest", headers=auth, json=[]).status_code == 403
