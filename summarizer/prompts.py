"""Prompt templates for Gemini summarization."""

AI_SIGNAL_PROMPT = """You are an investor intelligence analyst. Given these AI-related articles, select the top {top_n} most significant for a tech investor. Rank by signal strength (how likely this impacts markets, startups, or investment theses).

Articles:
{articles}

Return ONLY a JSON array. Each item must have:
- "title": original article title
- "url": original article URL
- "source": source name
- "summary": 2-sentence investor-focused summary (why this matters for money)
- "signal": "HIGH", "MEDIUM", or "LOW"

Sort by signal strength (HIGH first). Return valid JSON only, no markdown."""

YC_MEMO_PROMPT = """You are a VC analyst writing a quick investment memo. Given this YC company, produce a concise investor memo.

{company}

Return ONLY a JSON object with these fields:
- "problem": 1 sentence on the problem they solve
- "solution": 1 sentence on their approach
- "market": 1 sentence on market size / opportunity
- "why_now": 1 sentence on timing (why this works now)
- "signal": "HIGH", "MEDIUM", or "LOW" (how promising this company looks)

Be direct and analytical. Return valid JSON only, no markdown."""

MARKET_WIRE_PROMPT = """You are a financial news analyst. Given these fintech/market articles, select the top {top_n} most relevant for a tech-focused investor.

Articles:
{articles}

Return ONLY a JSON array. Each item must have:
- "title": original article title
- "url": original article URL
- "source": source name
- "summary": 2-sentence summary with investor implications
- "signal": "HIGH", "MEDIUM", or "LOW"

Sort by signal strength (HIGH first). Return valid JSON only, no markdown."""
