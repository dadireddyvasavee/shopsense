"""Query understanding: natural language -> structured, catalog-validated search parameters."""
import re

from app.core import llm
from app.schemas import ParsedQuery

SYNONYMS = {
    "laptops": ["laptop", "notebook", "macbook", "ultrabook", "chromebook"],
    "shoes": ["shoe", "shoes", "sneaker", "sneakers", "footwear", "loafer", "trainers"],
    "skincare": ["skincare", "skin care", "moisturizer", "moisturiser", "sunscreen", "serum", "cleanser", "face wash"],
    "smartphones": ["phone", "smartphone", "mobile"],
    "audio": ["earbuds", "headphones", "headphone", "earphones", "neckband", "audio"],
}
_NUM = r"(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d+)?)\s*(k|thousand|lakh)?"
_STOP = set(llm.STOPWORDS) | {"find", "recommend", "suggest", "need", "want", "looking", "show", "under", "below",
                              "less", "than", "within", "budget", "around", "best", "good", "rs", "inr", "some", "products",
                              "product", "suitable", "compare", "between", "vs", "versus", "over", "above", "max", "maximum"}


def _num(m: re.Match) -> float:
    v = float(m.group(1).replace(",", ""))
    unit = (m.group(2) or "").lower()
    return v * 1000 if unit in ("k", "thousand") else v * 100000 if unit == "lakh" else v


def rule_parse(text: str, brands: list[str]) -> ParsedQuery:
    t = text.lower()
    q = ParsedQuery(method="rules")
    if m := re.search(r"between\s+" + _NUM + r"\s+(?:and|to|-)\s+" + _NUM, t):
        a = _num(m)
        b = float(m.group(3).replace(",", "")) * (1000 if (m.group(4) or "").lower() in ("k", "thousand") else 1)
        q.budget_min, q.budget_max = min(a, b), max(a, b)
    elif m := re.search(r"(?:under|below|less than|within|upto|up to|max(?:imum)?|budget(?: of)?|<)\s*" + _NUM, t):
        q.budget_max = _num(m)
    elif m := re.search(r"(?:over|above|more than|>)\s*" + _NUM, t):
        q.budget_min = _num(m)
    for cat, words in SYNONYMS.items():
        if any(re.search(rf"\b{re.escape(w)}\b", t) for w in words):
            q.category = cat
            break
    q.brands = [b for b in brands if re.search(rf"\b{re.escape(b.lower())}\b", t)]
    if re.search(r"\b(compare|vs|versus)\b", t):
        q.intent = "compare"
    if m := re.search(r"(\d+)\s*gb\s*ram", t):
        q.required_specs["ram_gb"] = int(m.group(1))
    no_nums = re.sub(_NUM, " ", t)
    cat_words = {w for ws in SYNONYMS.values() for w in ws}
    q.keywords = [w for w in llm.tokenize(no_nums) if w not in _STOP and w not in cat_words
                  and w not in {b.lower() for b in brands} and not w.isdigit() and len(w) > 2]
    return q


def understand(text: str, categories: list[str], brands: list[str]) -> ParsedQuery:
    base = rule_parse(text, brands)
    if not llm.llm_configured():
        return base
    try:
        out = llm.chat_json([
            {"role": "system", "content": (
                "Extract shopping search parameters. Respond ONLY with JSON having keys: category (one of "
                f"{categories} or null), budget_min (number INR or null), budget_max (number INR or null), "
                f"brands (subset of {brands}), keywords (list of short preference words, e.g. 'programming', "
                "'walking', 'oily skin'), required_specs (object, e.g. {\"ram_gb\": 16}), intent ('search' or 'compare').")},
            {"role": "user", "content": text}])
    except llm.LLMUnavailable:
        return base
    # Validate LLM output against the real catalog; never trust unknown values.
    cat = out.get("category") if out.get("category") in categories else base.category
    def money(v):
        return float(v) if isinstance(v, (int, float)) and v > 0 else None
    return ParsedQuery(
        category=cat,
        budget_min=money(out.get("budget_min")) or base.budget_min,
        budget_max=money(out.get("budget_max")) or base.budget_max,
        brands=[b for b in out.get("brands", []) if b in brands] or base.brands,
        keywords=[str(k).lower() for k in out.get("keywords", []) if isinstance(k, str)][:8] or base.keywords,
        required_specs={k: v for k, v in (out.get("required_specs") or {}).items() if isinstance(v, (int, float, str, bool))},
        intent=out.get("intent") if out.get("intent") in ("search", "compare") else base.intent,
        method="llm+validated")
