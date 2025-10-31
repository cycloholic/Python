# FeedWizard  
AI-Ready Product Feed ETL Pipeline

FeedWizard is a modular Python pipeline for ingesting, validating, and enriching e-commerce product feeds — designed with clean architecture, data quality principles, and AI-first workflows in mind.

It demonstrates:

- ✅ Feed ingestion & schema-driven parsing (Polars)
- ✅ Data validation with Pydantic
- ✅ SQLAlchemy ORM to SQLite storage
- ✅ Clear module separation (reader / models / db / main)
- ✅ AI-ready title & content enrichment (mock LLM layer)
- ✅ Bonus script for marketing content generation from the feed
- ✅ Production-thinking: scaling, architecture, future upgrades

---

##  Features

| Area | Focus |
|---|---|
ETL | Polars-based feed parsing, schema overrides, type casting  
Validation | Pydantic product model + structured issue logging  
Storage | SQLAlchemy ORM + SQLite (easily swappable to Postgres)  
AI Hooks | Prompt templates + strategy mock → real LLM integration  
Extras | Marketing content generator using same feed data  

---

## Architecture Thoughts (Scaling to production)



| Task                    | Idea                                                                 |
| ----------------------- | -------------------------------------------------------------------- |
| Google Ads headlines    | Generate 5 ad headlines max 30 chars using product title and brand   |
| Instagram captions      | Use product description + tone prompt                                |
| Weekly blog outline     | Turn category list into editorial calendar                           |
| Short-form video script | Hook → benefit bullets → CTA using product data                      |
