# database_handler.py
from __future__ import annotations
from typing import Iterable, Tuple, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Base, ProductORM, IssueORM, ProductModel


class Database:
    def __init__(self, db_path: str):
        """
        Note:
        The database URI/path is sensitive configuration.
        In production (e.g., Kubernetes), this should come through environment
        variables or Secrets/ConfigMaps — not hardcoded inside the service.
        """
        self.engine = create_engine(f"sqlite:///{db_path}", future=True)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(self.engine, future=True)

    def save(
        self,
        products: Iterable[Tuple[ProductModel, Optional[str]]],
        issues: Iterable[Tuple[str, str]]
    ):
        """
        Saves validated products and any detected issues to the database.

        - Uses SQLAlchemy `merge` → id-based UPSERT behavior
        - Ensures missing product IDs are handled safely
        - Commits once for efficiency
        """
        with self.Session() as s:
            # Store products (validated + optional improved title)
            for p, improved in products:
                s.merge(
                    ProductORM(
                        id=(p.id or ""),  # fallback to empty string if id missing
                        title=p.title,
                        improved_title=improved,
                        description=p.description,
                        price=p.price,
                        currency=p.currency,
                        gtin=p.gtin,
                        brand=p.brand,
                        image_url=str(p.image_url) if p.image_url else None,
                        product_url=str(p.product_url) if p.product_url else None,
                        category=p.category,
                        availability=p.availability,
                    )
                )

            # Store validation issues per product
            for pid, iss in issues:
                s.merge(IssueORM(id=(pid or ""), issue=iss))

            s.commit()
