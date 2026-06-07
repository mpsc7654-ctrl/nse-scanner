"""
AI is used ONLY for generating natural-language market summaries.
All signal logic is deterministic (indicators.py + scanner.py).
"""
import anthropic
from app.core.config import settings
from app.core.redis_client import cache_get, cache_set

_client = None

def get_client():
    global _client
    if _client is None and settings.ANTHROPIC_API_KEY:
        _client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    return _client

async def generate_market_summary(signals: list[dict]) -> str:
    """Generate a short market summary from signal data. Cached for 15 min."""
    cached = await cache_get("ai:market_summary")
    if cached:
        return cached.get("summary", "")

    client = get_client()
    if not client:
        return _fallback_summary(signals)

    buy_count = sum(1 for s in signals if "BUY" in s.get("signal", ""))
    sell_count = sum(1 for s in signals if "SELL" in s.get("signal", ""))
    top_buys = [s["symbol"] for s in signals if s.get("signal") == "STRONG_BUY"][:5]
    top_sells = [s["symbol"] for s in signals if s.get("signal") == "STRONG_SELL"][:5]

    prompt = f"""You are a stock market analyst. Given these scanner results for NSE F&O stocks, write a 3-sentence market summary in plain English.

Data:
- Total scanned: {len(signals)} F&O stocks
- Strong Buy signals: {buy_count} stocks (top: {', '.join(top_buys) if top_buys else 'none'})
- Strong Sell signals: {sell_count} stocks (top: {', '.join(top_sells) if top_sells else 'none'})
- Market breadth: {"bullish" if buy_count > sell_count else "bearish" if sell_count > buy_count else "neutral"}

Write 3 concise sentences: overall market tone, key opportunities, key risks. No disclaimers."""

    try:
        response = await client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )
        summary = response.content[0].text
        await cache_set("ai:market_summary", {"summary": summary}, ttl=900)
        return summary
    except Exception:
        return _fallback_summary(signals)

async def generate_stock_summary(symbol: str, data: dict) -> str:
    """Generate a stock-specific 2-line insight. Cached per symbol for 10 min."""
    cache_key = f"ai:stock_summary:{symbol}"
    cached = await cache_get(cache_key)
    if cached:
        return cached.get("summary", "")

    client = get_client()
    if not client:
        return f"{symbol}: {data.get('signal','NEUTRAL')} signal with {data.get('confidence',50):.0f}% confidence."

    prompt = f"""Stock analysis for {symbol} on NSE F&O. Write exactly 2 sentences: one about the current setup, one about the trade opportunity.

Signal: {data.get('signal')}
Price: ₹{data.get('price')}
RSI: {data.get('rsi14')}
MACD Hist: {data.get('macd',0):.3f}
EMA20/100: ₹{data.get('ema20')}/₹{data.get('ema100')}
Support: ₹{data.get('support1')} | Resistance: ₹{data.get('resistance1')}
Entry: ₹{data.get('entry')} | SL: ₹{data.get('stoploss')} | T1: ₹{data.get('target1')}
Reasoning: {data.get('reasoning','')}

Be specific. No generic advice."""

    try:
        response = await client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=120,
            messages=[{"role": "user", "content": prompt}]
        )
        summary = response.content[0].text
        await cache_set(cache_key, {"summary": summary}, ttl=600)
        return summary
    except Exception:
        return f"{symbol}: {data.get('signal','NEUTRAL')} at ₹{data.get('price',0):.2f}."

def _fallback_summary(signals: list[dict]) -> str:
    buy_count = sum(1 for s in signals if "BUY" in s.get("signal", ""))
    sell_count = sum(1 for s in signals if "SELL" in s.get("signal", ""))
    tone = "bullish" if buy_count > sell_count else "bearish" if sell_count > buy_count else "mixed"
    return (f"Market breadth is {tone} with {buy_count} buy signals and {sell_count} sell signals "
            f"across {len(signals)} F&O stocks. Monitor high-conviction signals with volume confirmation.")
