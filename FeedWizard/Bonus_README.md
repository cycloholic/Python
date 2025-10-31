What I built

FeedWizard: ETL pipeline για e-commerce feed (CSV → Polars → Pydantic validation → SQLite via SQLAlchemy ORM).

Validation κανόνες: price/gtin/image/title.

AI-first workflow: mock title improver + prompt templates για marketing περιεχόμενο.

Extra: marketing_ai.py που επαναχρησιμοποιεί το ίδιο feed για Google Ads, Instagram captions, blog outline, video scripts.

What I’d do next (with more time)

Real LLM integration (provider switch via env flag: MOCK|OPENAI|MISTRAL|OLLAMA).

Async ingestion (aiohttp) + retries/backoff + circuit breakers.

Export to Parquet/S3 + DuckDB για analytics, ή Postgres για OLTP.

Stream processing (Kafka) για incremental updates.

A/B testing σε τίτλους (LLM variants) + click-through rate feedback loop.

Feature flags (e.g., “ai_title_enabled”) ανά κατηγορία.

Bonus ideas

SEO score per title (length, brand, modifiers) + auto-tuning.

Category-aware prompting (π.χ. “Strength Training” vs “Cardio” voice).

Visual creatives: image prompt stubs per product (για image gen tool).

Multi-language captions (SV/EN/EL) με locale-aware hashtags.
