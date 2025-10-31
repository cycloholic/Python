# models.py
from __future__ import annotations
import re
from typing import Optional, List

from pydantic import BaseModel, HttpUrl, field_validator

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Float

# ---------- SQLAlchemy Base ----------
class Base(DeclarativeBase):
    pass

# ---------- ORM models ----------
class ProductORM(Base):
    __tablename__ = "products"

    # ΠΡΕΠΕΙ να υπάρχει PK
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
    __tablename__ = "issues"
    # composite PK: (id, issue)
    id: Mapped[str] = mapped_column(String, primary_key=True)
    issue: Mapped[str] = mapped_column(String, primary_key=True)

# ---------- Pydantic model ----------
class ProductModel(BaseModel):
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

    @field_validator("price", mode="before")
    @classmethod
    def parse_price(cls, v):
        if v is None or str(v).strip() == "":
            return None
        try:
            return float(str(v).replace(",", "."))
        except Exception:
            return None

    @field_validator("gtin", mode="before")
    @classmethod
    def normalize_gtin(cls, v):
        """Το feed βάζει στο EAN και κείμενα τύπου 'identifier_exists = no'.
        Κρατάμε μόνο ψηφία (8/12/13/14)."""
        if not v:
            return None
        digits = re.sub(r"\D", "", str(v))
        if len(digits) in (8, 12, 13, 14):
            return digits
        return None

    @field_validator("image_url", "product_url", mode="before")
    @classmethod
    def empty_url_to_none(cls, v):
        s = (str(v).strip() if v is not None else "")
        return s or None

def validate_product(p: ProductModel) -> List[str]:
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
