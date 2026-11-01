from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class TS:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class User(TS, Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="shopper")


class Category(TS, Base):
    __tablename__ = "categories"
    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))


class Product(TS, Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(primary_key=True)
    sku: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), index=True)
    brand: Mapped[str] = mapped_column(String(100), index=True)
    description: Mapped[str] = mapped_column(Text)
    price: Mapped[float] = mapped_column(Float, index=True)
    specifications: Mapped[dict] = mapped_column(JSON, default=dict)
    attributes: Mapped[list] = mapped_column(JSON, default=list)
    image_url: Mapped[str | None] = mapped_column(String(500))
    source: Mapped[str] = mapped_column(String(50), default="demo")  # demo dataset, not live inventory
    embedding: Mapped[list] = mapped_column(JSON, default=list)
    category: Mapped[Category] = relationship(lazy="joined")


class UserPreference(TS, Base):
    __tablename__ = "user_preferences"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    budget_max: Mapped[float | None] = mapped_column(Float)
    favorite_categories: Mapped[list] = mapped_column(JSON, default=list)
    favorite_brands: Mapped[list] = mapped_column(JSON, default=list)
    interests: Mapped[list] = mapped_column(JSON, default=list)


class BrowsingHistory(TS, Base):
    __tablename__ = "browsing_history"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)


class SavedProduct(TS, Base):
    __tablename__ = "saved_products"
    __table_args__ = (UniqueConstraint("user_id", "product_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    product: Mapped[Product] = relationship(lazy="joined")


class ProductInteraction(TS, Base):
    __tablename__ = "product_interactions"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(20))  # view|save|like|dislike|compare
    weight: Mapped[float] = mapped_column(Float, default=1.0)


class Recommendation(TS, Base):
    __tablename__ = "recommendations"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    score: Mapped[float] = mapped_column(Float)
    reasons: Mapped[list] = mapped_column(JSON, default=list)
    context: Mapped[str] = mapped_column(String(50), default="home")  # home|assistant
    saved: Mapped[int] = mapped_column(Integer, default=0)
    product: Mapped[Product] = relationship(lazy="joined")


class ProductComparison(TS, Base):
    __tablename__ = "product_comparisons"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    product_ids: Mapped[list] = mapped_column(JSON)
    summary: Mapped[str] = mapped_column(Text)
    summary_method: Mapped[str] = mapped_column(String(20))


class AssistantTurn(TS, Base):
    __tablename__ = "assistant_turns"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    query: Mapped[str] = mapped_column(Text)
    parsed: Mapped[dict] = mapped_column(JSON)
    reply: Mapped[str] = mapped_column(Text)
    product_ids: Mapped[list] = mapped_column(JSON, default=list)
