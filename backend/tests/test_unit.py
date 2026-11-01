from app.services.query import rule_parse

BRANDS = ["Nimbus", "Voltra", "Kestrel", "Orbita", "Stride", "Pacelyn"]


def test_parse_budget_category_keywords():
    q = rule_parse("Find a laptop under ₹70,000 for programming", BRANDS)
    assert q.category == "laptops" and q.budget_max == 70000 and "programming" in q.keywords


def test_parse_k_suffix_range_and_brand():
    q = rule_parse("Voltra phone between 15k and 25k with 8 gb ram", BRANDS)
    assert q.category == "smartphones" and (q.budget_min, q.budget_max) == (15000, 25000)
    assert q.brands == ["Voltra"] and q.required_specs == {"ram_gb": 8}


def test_parse_compare_intent_and_shoes():
    assert rule_parse("compare Stride vs Pacelyn shoes", BRANDS).intent == "compare"
    q = rule_parse("Recommend comfortable shoes for daily walking", BRANDS)
    assert q.category == "shoes" and {"comfortable", "walking"} <= set(q.keywords)
