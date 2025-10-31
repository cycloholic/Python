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

If this prototype grew into a real system processing thousands of SKUs/day:


-Database	      PostgreSQL or BigQuery for scale. SQLite is fine for local dev & interviews.
-Processing	    Batch ingestion (hourly / daily) or streaming with Kafka if near-real-time is needed.
-Error Handling	Store rejected records in failed_products table for manual review + alerting.
-Secrets	      DB paths & API keys in environment variables or Kubernetes secrets.
-AI Strategy	  Enrich titles, generate marketing copy, auto-fix missing metadata.
