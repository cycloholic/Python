# main.py
from __future__ import annotations
import re, textwrap
from typing import List, Dict, Optional, Tuple
import polars as pl

from csv_reader import fetch_csv
from models import ProductModel, validate_product
from database_handler import Database

FEED_URL = "https://hefitness.se/csv/"
DB_PATH = "products.db"


# ---- AI mock logic ----
def build_title_prompt(p: ProductModel) -> str:
    """
    Build a prompt for improving a product title.
    In a real setup this would be sent to an LLM.
    """
    return textwrap.dedent(f"""
    Improve this e-commerce product title.
    Rules: <= 70 chars, include brand if present.
    Current title: "{(p.title or "").strip()}"
    Brand: {(p.brand or "").strip() or "N/A"}
    Category: {(p.category or "").strip() or "N/A"}
    """)

def fake_ai_call(prompt: str) -> str:
    """
    Simple heuristic to simulate AI output.
    Extracts product brand/title and formats a cleaner version.
    """
    import re as _re
    brand_m = _re.search(r"Brand:\s*(.*)", prompt)
    base_m = _re.search(r'Current title:\s*"(.*)"', prompt)
    brand = (brand_m.group(1).strip() if brand_m else "")
    base = (base_m.group(1).strip() if base_m else "")
    parts = []
    if brand and brand.lower() != "n/a":
        parts.append(brand.strip())
    if base:
        parts.append(base)
    new_title = " ".join(parts) if parts else (brand or base or "Product")
    new_title = _re.sub(r"\s+", " ", new_title).strip().title()
    return (new_title[:67] + "…") if len(new_title) > 70 else new_title

def improve_title_if_needed(p: ProductModel) -> Optional[str]:
    """Return an improved title only if existing one is too short/weak."""
    if not p.title or len(p.title.strip()) < 12:
        return fake_ai_call(build_title_prompt(p))
    return None


# ---- Header normalization helpers ----
def normalize_key(s: str) -> str:
    """Convert feed column names to snake_case style keys."""
    return re.sub(r"\W+", "_", s).lower()

# Mapping feed headers → our canonical internal field names
RENAME_MAP = {
    "artnr": "id",
    "varugrupp": "category",
    "produktnamn": "title",
    "tillverkare": "brand",
    "modell": "model",
    "ean": "gtin",
    "lagersaldo": "stock",
    "pris": "price",
    "kampanjvara_1_0": "promo_flag",
    "frakt": "shipping_cost",
    "url": "product_url",
    "bildurl": "image_url",
    "beskrivning": "description",
}

def normalize_rows(headers: List[str], rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Normalize feed rows:
    - Convert keys to snake_case
    - Apply friendly field renaming via RENAME_MAP
    """
    norm = []
    norm_headers = [normalize_key(h) for h in headers]
    for row in rows:
        r = {}
        # using range() because we want raw index positions
        for i in range(len(headers)):
            key = norm_headers[i]
            val = row[headers[i]]
            r[key] = val
        r = {RENAME_MAP.get(k, k): v for k, v in r.items()}
        norm.append(r)
    return norm


# ---- Explicit DataFrame schema ----
DF_SCHEMA = pl.Schema({
    "id": pl.String,
    "category": pl.String,
    "title": pl.String,
    "brand": pl.String,
    "model": pl.String,
    "gtin": pl.String,          # cleaned further by Pydantic
    "stock": pl.Int64,
    "price": pl.Float64,
    "promo_flag": pl.String,     # raw "1"/"0" -> treated as string here
    "shipping_cost": pl.String,  # not critical, kept as string
    "product_url": pl.String,
    "image_url": pl.String,
    "description": pl.String,
})

def to_dataframe(records: List[Dict[str, str]]) -> pl.DataFrame:
    """
    Convert raw dict records into a typed Polars DataFrame.
    Includes safe casting for numeric fields and derived flags.
    """
    df = pl.DataFrame(records, schema_overrides=DF_SCHEMA, strict=False)

    # Handle price safely whether it's string or already numeric
    if "price" in df.columns:
        if df["price"].dtype == pl.Utf8:
            df = df.with_columns(
                pl.col("price").str.replace(",", ".").cast(pl.Float64, strict=False)
            )
        else:
            df = df.with_columns(pl.col("price").cast(pl.Float64, strict=False))

    # Ensure stock is integer
    if "stock" in df.columns:
        if df["stock"].dtype != pl.Int64:
            df = df.with_columns(pl.col("stock").cast(pl.Int64, strict=False))

    # Derived availability field
    if "stock" in df.columns:
        df = df.with_columns(
            pl.when(pl.col("stock") > 0)
            .then(pl.lit("in_stock"))
            .otherwise(pl.lit("out_of_stock"))
            .alias("availability")
        )
    else:
        df = df.with_columns(pl.lit("unknown").alias("availability"))

    # Add currency default
    df = df.with_columns(pl.lit("SEK").alias("currency"))
    return df


# ---- Main ETL flow ----
def main():
    print("Downloading & reading feed…")
    headers, rows = fetch_csv(FEED_URL)

    # Normalize header names & row keys
    records = normalize_rows(headers, rows)

    # Create typed Polars DataFrame
    df = to_dataframe(records)

    print("Columns:", df.columns)
    print("Rows:", df.height)
    print(df.head(3))

    total = flagged = improved_count = 0
    example_improved = None

    products_for_db: List[Tuple[ProductModel, Optional[str]]] = []
    issues_for_db: List[Tuple[str, str]] = []

    # Validate + optionally "AI-improve" titles
    for row in df.iter_rows(named=True):
        total += 1
        p = ProductModel(**row)

        improved = improve_title_if_needed(p)
        if improved:
            improved_count += 1
            if example_improved is None:
                example_improved = improved

        for iss in validate_product(p):
            flagged += 1
            issues_for_db.append((p.id or "", iss))

        products_for_db.append((p, improved))

    #  In production: DB path should come from env/secret, not hardcoded
    db = Database(DB_PATH)
    db.save(products_for_db, issues_for_db)

    print("\n--- SUMMARY ---")
    print("Total products:", total)
    print("Products with issues:", flagged)
    print("Titles improved (mock AI):", improved_count)
    print("Example improved title:", example_improved)
    print(f"Saved to SQLite: {DB_PATH}")


if __name__ == "__main__":
    main()
