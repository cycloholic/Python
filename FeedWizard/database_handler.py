# database_handler.py
from __future__ import annotations
from typing import Iterable, Tuple, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Base, ProductORM, IssueORM, ProductModel

class Database:
    def __init__(self, db_path: str):
        """
        ⚠️ Σημαντικό: Το path/URI της βάσης είναι ευαίσθητο.
        Σε production (π.χ. Kubernetes) πρέπει να παρέχεται από Secret/ConfigMap
        μέσω μεταβλητής περιβάλλοντος, όχι hardcoded μέσα στο service.
        """
        self.engine = create_engine(f"sqlite:///{db_path}", future=True)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(self.engine, future=True)

    def save(self,
             products: Iterable[Tuple[ProductModel, Optional[str]]],
             issues:   Iterable[Tuple[str, str]]):
        with self.Session() as s:
            for p, improved in products:
                s.merge(  # merge για id-based upsert
                    ProductORM(
                        id=(p.id or ""),
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
            for pid, iss in issues:
                s.merge(IssueORM(id=(pid or ""), issue=iss))
            s.commit()
