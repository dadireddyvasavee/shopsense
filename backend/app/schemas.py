from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class RegisterIn(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=8)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(ORM):
    id: int
    email: str
    full_name: str
    role: str


class CategoryOut(ORM):
    id: int
    slug: str
    name: str


class ProductOut(ORM):
    id: int
    sku: str
    name: str
    brand: str
    description: str
    price: float
    specifications: dict
    attributes: list[str]
    image_url: str | None
    source: str
    category: CategoryOut


class ScoredProduct(BaseModel):
    product: ProductOut
    score: float
    reasons: list[str]
    rec_id: int | None = None  # persisted Recommendation id (can be saved)


class PreferencesIO(ORM):
    budget_max: float | None = Field(default=None, ge=0)
    favorite_categories: list[str] = []
    favorite_brands: list[str] = []
    interests: list[str] = []


class InteractionIn(BaseModel):
    kind: str = Field(pattern="^(like|dislike)$")


class CompareIn(BaseModel):
    product_ids: list[int] = Field(min_length=2, max_length=4)


class AssistantIn(BaseModel):
    message: str = Field(min_length=2, max_length=1000)


class ParsedQuery(BaseModel):
    category: str | None = None
    budget_max: float | None = None
    budget_min: float | None = None
    brands: list[str] = []
    keywords: list[str] = []
    required_specs: dict = {}
    intent: str = "search"  # search|compare
    method: str = "rules"


class AssistantOut(BaseModel):
    reply: str
    reply_method: str
    parsed: ParsedQuery
    results: list[ScoredProduct]


class CompareOut(BaseModel):
    id: int
    products: list[ProductOut]
    spec_keys: list[str]
    summary: str
    summary_method: str
    created_at: datetime
