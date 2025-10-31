# models.py
from __future__ import annotations
import re
from typing import Optional, List

from pydantic import BaseModel, HttpUrl, field_validator

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Float


# ---------- SQLAlchemy Base ----------
class Base(DeclarativeBase):
    """Base class used by SQLAlchemy ORM to track mapped models."""
    pass


# ---------- ORM models: Database Tables ----------
class ProductORM(Base):
    """
    SQLAlchemy ORM model for product records.
    SQLite table storing the normalized product feed.
    """
    __tablename__ = "products"

    # Primary key is required in SQLAlchemy
    id: Mapped[str] = mapped_column(String, primary_key=True)

    title: Mapped[Optional[str]] = mapped_column(String)
    improved_title: Mapped[Optional[str]] = mapped_column(String)
    description: Mapped[Optional[str]] = mapped_column(String)
    price: Mapped[Optional[float]] = mapped_column(Float)
    currency: Mapped[Optional[str]] = mapped_column(String)
    gtin: Mapped[Optional[str]] = mapped_column(String)
    brand: Mapped[Optional[str]] = mapped_column(String)
    image_url: Mapped[Optional[str]] = mapped_column(String)
    product_url: Mapped[Optional[str]] = mapped_column(String)
    category: Mapped[Optional[str]] = mapped_column(String)
    availability: Mapped[Optional[str]] = mapped_column(String)


class IssueORM(Base):
    """
    Table for logging validation issues found in the feed data.
    Composite primary key = (product_id + issue_type).
    """
    __tablename__ = "issues"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    issue: Mapped[str] = mapped_column(String, primary_key=True)


# ---------- Pydantic Product Schema ----------
class ProductModel(BaseModel):
    """
    Pydantic model used for validation and type-safe handling
    before saving data to the database.
    """

    id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    gtin: Optional[str] = None
    brand: Optional[str] = None

    image_url: Optional[HttpUrl] = None
    product_url: Optional[HttpUrl] = None

    category: Optional[str] = None
    availability: Optional[str] = None

    # ---------- Custom field normalization / validation ----------

    @field_validator("price", mode="before")
    @classmethod
    def parse_price(cls, v):
        """
        Convert price values like "199,99" -> 199.99,
        and handle missing or malformed price strings gracefully.
        """
        if v is None or str(v).strip() == "":
            return None
        try:
            return float(str(v).replace(",", "."))
        except Exception:
            return None

    @field_validator("gtin", mode="before")
    @classmethod
    def normalize_gtin(cls, v):
        """
        The feed sometimes places text in the EAN field (e.g. 'identifier_exists=no').
        We keep only numeric characters and accept GTIN lengths commonly used in retail
        (8, 12, 13, 14 digits).
        """
        if not v:
            return None
        digits = re.sub(r"\D", "", str(v))
        if len(digits) in (8, 12, 13, 14):
            return digits
        return None

    @field_validator("image_url", "product_url", mode="before")
    @classmethod
    def empty_url_to_none(cls, v):
        """
        Treat empty string URLs as None so Pydantic HttpUrl validator won't fail.
        """
        s = (str(v).strip() if v is not None else "")
        return s or None


# ---------- Business Validation Logic ----------
def validate_product(p: ProductModel) -> List[str]:
    """
    Business-level validation rules for detecting missing/weak product data.
    These flags can be used for reporting or prompting AI improvement steps.
    """
    issues: List[str] = []

    if p.price is None or p.price <= 0:
        issues.append("missing_or_invalid_price")

    if not p.gtin or len(p.gtin) not in (8, 12, 13, 14):
        issues.append("missing_or_invalid_gtin")

    if not p.image_url:
        issues.append("missing_image_url")

    if not p.title or len(p.title.strip()) < 4:
        issues.append("weak_title")

    return issues
