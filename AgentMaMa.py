# main.py
from __future__ import annotations

import re
import sqlite3
import textwrap
from typing import Optional, List, Dict

import requests
import polars as pl
from pydantic import BaseModel, HttpUrl, field_validator

FEED_URL = "https://hefitness.se/csv/"
DB_PATH = "products.db"

# ------------------------------
# Robust CSV parsing για ';' με quotes & newlines
# ------------------------------
def _split_semicolon_line(line: str, expected_cols: int | None = None) -> list[str]:
    fields: List[str] = []
    cur: List[str] = []
    in_quote = False
    i = 0
    while i < len(line):
        ch = line[i]
        if ch == '"':
            if i + 1 < len(line) and line[i + 1] == '"':
                cur.append('"')
                i += 2
                continue
            in_quote = not in_quote
            i += 1
            continue
        if ch == ';' and not in_quote:
            fields.append(''.join(cur))
            cur = []
            i += 1
            continue
        cur.append(ch)
        i += 1
    fields.append(''.join(cur))

    if expected_cols is not None and len(fields) < expected_cols:
        fields += [''] * (expected_cols - len(fields))
    if expected_cols is not None and len(fields) > expected_cols:
        head = fields[: expected_cols - 1]
        tail_joined = ';'.join(fields[expected_cols - 1 :])
        fields = head + [tail_joined]
    return fields


def _parse_semicolon_csv(text: str) -> tuple[list[str], list[list[str]]]:
    lines = text.splitlines()
    if not lines:
        raise ValueError("Empty CSV")

    header_line = lines[0]
    headers = _split_semicolon_line(header_line)
    expected = len(headers)

    rows: List[List[str]] = []
    buf_chars: List[str] = []
    in_quote = False

    offset = len(header_line) + 1
    for ch in text[offset:]:
        if ch == '"':
            in_quote = not in_quote
            buf_chars.append(ch)
            continue
        if ch == '\n' and not in_quote:
            line = ''.join(buf_chars)
            if line:
                rows.append(_split_semicolon_line(line, expected_cols=expected))
            buf_chars = []
            continue
        buf_chars.append(ch)

    if buf_chars:
        line = ''.join(buf_chars)
        if line:
            rows.append(_split_semicolon_line(line, expected_cols=expected))

    return headers, rows


# ------------------------------
# Fetch feed -> Polars DataFrame
# ------------------------------
def fetch_feed(url: str) -> pl.DataFrame:
    print("Downloading feed...")
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    text = r.content.decode("utf-8", errors="replace")

    headers, rows = _parse_semicolon_csv(text)

    data_dict = {h: [row[i] if i < len(row) else "" for row in rows] for i, h in enumerate(headers)}
    df = pl.DataFrame(data_dict)

    # Cast βασικών numeric πριν το rename
    if "Pris" in df.columns:
        df = df.with_columns(pl.col("Pris").str.replace(",", ".").cast(pl.Float64, strict=False))
    if "Lagersaldo" in df.columns:
        df = df.with_columns(pl.col("Lagersaldo").cast(pl.Int64, strict=False))

    return df


# ------------------------------
# Normalize (Σουηδικά -> canonical) & derived fields
# ------------------------------
def normalize_columns(df: pl.DataFrame) -> pl.DataFrame:
    df = df.rename({c: re.sub(r"\W+", "_", c).lower() for c in df.columns})

    rename_map = {
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
    df = df.rename({c: rename_map.get(c, c) for c in df.columns})

    if "stock" in df.columns:
        df = df.with_columns(
            pl.when(pl.col("stock").cast(pl.Int64, strict=False) > 0)
            .then(pl.lit("in_stock"))
            .otherwise(pl.lit("out_of_stock"))
            .alias("availability")
        )
    else:
        df = df.with_columns(pl.lit("unknown").alias("availability"))

    df = df.with_columns(pl.lit("SEK").alias("currency"))
    return df


# ------------------------------
# Pydantic model & validation
# ------------------------------
class Product(BaseModel):
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

    @field_validator("gtin")
    @classmethod
    def normalize_gtin(cls, v):
        if not v:
            return v
        digits = re.sub(r"\D", "", str(v))
        return digits or None

    @field_validator("image_url", "product_url", mode="before")
    @classmethod
    def empty_url_to_none(cls, v):
        if v is None:
            return None
        s = str(v).strip()
        return s or None


def validate_product(p: Product) -> List[str]:
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


# ------------------------------
# Mock AI βελτίωση τίτλων
# ------------------------------
def build_title_prompt(p: "Product") -> str:
    return textwrap.dedent(f"""
    Improve this e-commerce product title.
    Constraints: <= 70 chars, include brand if present.
    Current title: "{(p.title or "").strip()}"
    Brand: {(p.brand or "").strip() or "N/A"}
    Category: {(p.category or "").strip() or "N/A"}
    """)

def fake_ai_call(prompt: str) -> str:
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

def improve_title_if_needed(p: "Product") -> str | None:
    if not p.title or len(p.title.strip()) < 12:
        prompt = build_title_prompt(p)
        return fake_ai_call(prompt)
    return None


# ------------------------------
# SQLite helpers
# ------------------------------
def init_db(conn: sqlite3.Connection):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id TEXT,
            title TEXT,
            improved_title TEXT,
            description TEXT,
            price REAL,
            currency TEXT,
            gtin TEXT,
            brand TEXT,
            image_url TEXT,
            product_url TEXT,
            category TEXT,
            availability TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS issues (
            id TEXT,
            issue TEXT
        )
    """)

def save_products(conn: sqlite3.Connection, rows: List[tuple]):
    conn.executemany("""
        INSERT INTO products
        (id, title, improved_title, description, price, currency, gtin, brand, image_url, product_url, category, availability)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
    """, rows)

def save_issues(conn: sqlite3.Connection, rows: List[tuple]):
    if rows:
        conn.executemany("INSERT INTO issues (id, issue) VALUES (?,?)", rows)


# ------------------------------
# Main
# ------------------------------
def main():
    df = fetch_feed(FEED_URL)
    df = normalize_columns(df)

    print("\nColumns:", df.columns)
    print("Rows:", df.height)
    print("\nHead:")
    print(df.head(3))

    total = 0
    flagged = 0
    examples: List[Dict] = []

    improved_count = 0
    example_improved: str | None = None

    product_rows: List[tuple] = []
    issue_rows: List[tuple] = []

    for row in df.iter_rows(named=True):
        total += 1
        p = Product(**row)

        # Mock AI improve
        improved = improve_title_if_needed(p)
        if improved:
            improved_count += 1
            if example_improved is None:
                example_improved = improved

        # Validation
        issues = validate_product(p)
        if issues:
            flagged += 1
            if len(examples) < 5:
                examples.append({"id": p.id, "title": p.title, "issues": issues})
            for i in issues:
                issue_rows.append((p.id or "", i))

        product_rows.append((
            p.id, p.title, improved, p.description, p.price, p.currency, p.gtin, p.brand,
            str(p.image_url) if p.image_url else None,
            str(p.product_url) if p.product_url else None,
            p.category, p.availability
        ))

    # Save to SQLite
    conn = sqlite3.connect(DB_PATH)
    with conn:
        init_db(conn)
        save_products(conn, product_rows)
        save_issues(conn, issue_rows)

    print("\n--- SUMMARY ---")
    print("Total products:", total)
    print("Products with issues:", flagged)
    print("Titles improved (mock AI):", improved_count)
    print("Example improved title:", example_improved)
    print(f"\nSaved to SQLite: {DB_PATH} (tables: products, issues)")


if __name__ == "__main__":
    main()
