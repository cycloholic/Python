# marketing_ai.py
from __future__ import annotations

import sqlite3
import textwrap
from typing import Dict, List, Tuple, Optional


DB_PATH = "products.db"


# ---------- Mock AI + Prompt Templates ----------
def mock_llm(prompt: str) -> str:
    """
    Lightweight mock LLM function.
    In a real deployment this would call OpenAI/Mistral/Ollama/etc.
    
    Here we simulate "AI-like" output by summarizing the last part
    of the prompt so we can demo the pipeline without API credentials.
    """
    lines = [ln.strip() for ln in prompt.splitlines() if ln.strip()]
    base = " ".join(lines[-3:])[:240]
    return f"[MOCK_AI_OUT] {base} ..."


def llm_call_pseudocode(provider: str, prompt: str) -> str:
    """
    Pseudocode showing how real LLM calls would be integrated.

    Example (OpenAI):
        from openai import OpenAI
        client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role":"system","content":"You are a marketing copywriter."},
                {"role":"user","content": prompt}
            ],
            max_tokens=150,
            temperature=0.7
        )
        return res.choices[0].message.content

    This function still returns mock output for this demo.
    """
    return mock_llm(prompt)


# ---------- Prompt builders ----------
def prompt_google_headlines(title: str, brand: str, category: str, price: Optional[float]) -> str:
    """Prompt template for Google Ads headline generation."""
    return textwrap.dedent(f"""
    Task: Create 5 Google Ads headlines (<= 30 chars each) for an e-commerce product.
    Rules:
    - Clear benefit + buying intent
    - Include brand if useful
    - Use language relevant to {category or 'general'} shoppers
    - If price exists, you may include a price hook — but avoid currency symbols unless useful

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
    """Prompt for Instagram caption writing with a casual marketing tone."""
    return textwrap.dedent(f"""
    Task: Write an Instagram caption (~120 words max) for a product.
    Rules:
    - Friendly, energetic tone
    - Start with a hook
    - 3 short benefit bullets
    - End with 4–6 relevant hashtags (not spammy)

    Input:
      Title: {title}
      Brand: {brand or 'N/A'}
      Description (HTML): {desc_html[:800]}

    Output format:
    Hook line
    • Benefit 1
    • Benefit 2
    • Benefit 3
    Hashtags: #...
    """)


def prompt_weekly_blog_outline(categories: List[str]) -> str:
    """Prompt for generating a content calendar outline."""
    cats = ", ".join(sorted({c for c in categories if c}))
    return textwrap.dedent(f"""
    Task: Create a weekly blog outline (5 sections) for an e-commerce store.
    Theme categories: {cats or 'General Fitness'}

    Each section must have:
    - A title
    - 2–3 bullet points (educational or product-driven)
    - 1 call-to-action idea

    Output format:
    1) Title
       - Idea
       - Idea
       CTA:
    2) ...
    """)


def prompt_short_video_script(title: str, category: str, key_points: List[str]) -> str:
    """Prompt to generate a 20–30s TikTok/Shorts script."""
    bullets = "\n".join([f"- {p}" for p in key_points[:4]])
    return textwrap.dedent(f"""
    Task: Create a 20–30 second script for TikTok/YouTube Shorts.
    Style: quick cuts, up
