# marketing_ai.py
from __future__ import annotations

import sqlite3
import textwrap
from typing import Dict, List, Tuple, Optional


DB_PATH = "products.db"


# ---------- Mock AI + Prompt Templates ----------
def mock_llm(prompt: str) -> str:
    """Placeholder AI: συνοψίζει/συνδυάζει χωρίς εξωτερικό API.
    Σε πραγματικό LLM, αντικαθιστάς αυτό με κλήση στο provider."""
    # Πολύ απλό heuristic για demo
    lines = [ln.strip() for ln in prompt.splitlines() if ln.strip()]
    base = " ".join(lines[-3:])[:240]
    return f"[MOCK_AI_OUT] {base} ..."

def llm_call_pseudocode(provider: str, prompt: str) -> str:
    """
    ΠΩΣ θα το έκανες πραγματικά (παράδειγμα):
    - provider='openai':
        from openai import OpenAI
        client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])
        out = client.chat.completions.create(
            model='gpt-4o-mini',
            messages=[{'role':'system','content':'You are a marketing copywriter.'},
                      {'role':'user','content': prompt}],
            temperature=0.7,
            max_tokens=140
        )
        return out.choices[0].message.content
    - provider='mistral':
        ...
    - provider='ollama' (local):
        subprocess.run(['ollama', 'run', 'llama3', prompt], capture_output=True)
    """
    return mock_llm(prompt)


# ---------- Prompt builders ----------
def prompt_google_headlines(title: str, brand: str, category: str, price: Optional[float]) -> str:
    return textwrap.dedent(f"""
    Task: Create 5 Google Ads headlines (<= 30 chars each) for an e-commerce product.
    Rules:
    - Clear benefit + intent; no clickbait
    - Include brand if helpful
    - Use {category or 'General'} buyer language
    - If price exists, consider a price hook; avoid currency symbols unless helpful
    Input:
      Title: {title}
      Brand: {brand or 'N/A'}
      Category: {category or 'N/A'}
      Price: {price if price is not None else 'N/A'}
    Output format:
    1) ...
    2) ...
    3) ...
    4) ...
    5) ...
    """)

def prompt_instagram_caption(title: str, desc_html: str, brand: str) -> str:
    return textwrap.dedent(f"""
    Task: Write an Instagram caption (max ~120 words) for a product.
    Rules:
    - Friendly, energetic, no hard-sell
    - Start with a hook line
    - 3 short bullet-like lines with benefits
    - 4–6 relevant hashtags at the end (no spam)
    Input:
      Title: {title}
      Brand: {brand or 'N/A'}
      Description(HTML): {desc_html[:800]}
    Output format:
    Hook line
    • Benefit 1
    • Benefit 2
    • Benefit 3
    Hashtags: #...
    """)

def prompt_weekly_blog_outline(categories: List[str]) -> str:
    cats = ", ".join(sorted({c for c in categories if c}))
    return textwrap.dedent(f"""
    Task: Propose a 5-section weekly blog outline for an e-commerce store.
    Theme: Use these product categories as weekly topics: {cats or 'General Fitness'}
    Rules:
    - 5 sections; each with: title, 2–3 bullet ideas, and 1 CTA idea
    - Educational + lightly commercial
    Output format:
    1) Title
       - Idea
       - Idea
       CTA:
    2) ...
    3) ...
    4) ...
    5) ...
    """)

def prompt_short_video_script(title: str, category: str, key_points: List[str]) -> str:
    bullets = "\n".join([f"- {p}" for p in key_points[:4]])
    return textwrap.dedent(f"""
    Task: Create a 20–30s script for TikTok/YouTube Shorts about a product.
    Style: quick cuts, on-screen captions, upbeat voiceover
    Input:
      Product: {title}
      Category: {category or 'General'}
      Key points:
      {bullets if bullets else "- Quality\n- Value\n- One clear benefit"}
    Output format:
    [Hook 0–3s]: ...
    [Body 4–20s]: ...
    [CTA 21–30s]: ...
    On-screen captions: ...
    """)


# ---------- Data access ----------
def fetch_products(limit: int = 10) -> List[Dict]:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("""
        SELECT id, title, brand, category, price, description
        FROM products
        WHERE title IS NOT NULL AND title <> ''
        LIMIT ?
    """, (limit,))
    rows = cur.fetchall()
    con.close()
    return [dict(r) for r in rows]

def fetch_all_categories(limit: int = 1000) -> List[str]:
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT DISTINCT category FROM products LIMIT ?", (limit,))
    cats = [r[0] or "" for r in cur.fetchall()]
    con.close()
    return cats


# ---------- Runners ----------
def generate_google_ads_samples(n: int = 5) -> List[Tuple[str, str]]:
    items = fetch_products(n)
    out: List[Tuple[str, str]] = []
    for it in items:
        pr = prompt_google_headlines(it["title"], it.get("brand") or "", it.get("category") or "", it.get("price"))
        out.append((it["id"], llm_call_pseudocode("openai", pr)))
    return out

def generate_instagram_captions(n: int = 3) -> List[Tuple[str, str]]:
    items = fetch_products(n)
    out = []
    for it in items:
        pr = prompt_instagram_caption(it["title"], it.get("description") or "", it.get("brand") or "")
        out.append((it["id"], llm_call_pseudocode("openai", pr)))
    return out

def generate_weekly_blog_outline() -> str:
    cats = fetch_all_categories()
    pr = prompt_weekly_blog_outline(cats)
    return llm_call_pseudocode("openai", pr)

def generate_short_video_scripts(n: int = 3) -> List[Tuple[str, str]]:
    items = fetch_products(n)
    out = []
    for it in items:
        # απλές key points από τίτλο/brand/category
        keys = [k for k in [it.get("brand"), it.get("category"), "Value", "Benefit"] if k]
        pr = prompt_short_video_script(it["title"], it.get("category") or "", keys)
        out.append((it["id"], llm_call_pseudocode("openai", pr)))
    return out


# ---------- CLI demo ----------
def main():
    print("=== Google Ads Headlines ===")
    for pid, txt in generate_google_ads_samples(3):
        print(f"\n[{pid}]\n{txt}")

    print("\n=== Instagram Captions ===")
    for pid, txt in generate_instagram_captions(2):
        print(f"\n[{pid}]\n{txt}")

    print("\n=== Weekly Blog Outline ===")
    print(generate_weekly_blog_outline())

    print("\n=== Short Video Scripts ===")
    for pid, txt in generate_short_video_scripts(2):
        print(f"\n[{pid}]\n{txt}")

if __name__ == "__main__":
    main()
