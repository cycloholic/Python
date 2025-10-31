# Bonus: AI Content & Architecture Extensions

##  AI Creative Content Use Cases

Using the extracted product feed, the system can generate:

✅ Google Ads headlines  
✅ Instagram captions  
✅ Weekly blog outlines  
✅ Short-form video scripts (TikTok / Reels / YouTube Shorts)  

All content is generated based on real product fields:
- Title
- Category
- Brand
- Price
- Description / HTML body

Outputs are created using prompt templates + a mock LLM layer.

> Ready for plug-in to OpenAI / Mistral / Ollama by replacing `mock_llm()`.

---

## Architecture & Scaling Thoughts

### Data Flow

