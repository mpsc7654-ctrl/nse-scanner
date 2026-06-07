from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import Optional
from app.core.database import get_db, AsyncSessionLocal
from app.core.redis_client import cache_get, cache_set
from app.models.models import Signal, Indicator, Quote, Watchlist
from app.services.scanner import scanner_service
from app.services.ai_summary import generate_market_summary, generate_stock_summary
from app.services.nse_data import FNO_SYMBOLS, nse_service
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/scanner/signals")
async def get_all_signals(signal_filter: Optional[str] = None, min_confidence: float = 0, db: AsyncSession = Depends(get_db)):
    cached = await cache_get("scanner:all_signals")
    if cached:
        signals = cached.get("signals", [])
        if signal_filter:
            signals = [s for s in signals if s.get("signal") == signal_filter]
        if min_confidence > 0:
            signals = [s for s in signals if s.get("confidence", 0) >= min_confidence]
        return {"signals": signals, "updated_at": cached.get("updated_at"), "count": len(signals)}
    q = select(Signal).order_by(desc(Signal.timestamp)).limit(100)
    result = await db.execute(q)
    signals = [dict(row.__dict__) for row in result.scalars()]
    return {"signals": signals, "count": len(signals)}

@router.get("/scanner/symbol/{symbol}")
async def get_symbol_data(symbol: str, db: AsyncSession = Depends(get_db)):
    symbol = symbol.upper()
    cached = await cache_get(f"scanner:{symbol}")
    if cached:
        return cached
    raise HTTPException(status_code=404, detail=f"No data for {symbol}")

@router.post("/scanner/trigger")
async def trigger_scan(background_tasks: BackgroundTasks):
    async def _run_scan():
        async with AsyncSessionLocal() as db_:
            await scanner_service.run_full_scan(db_)
    background_tasks.add_task(_run_scan)
    return {"message": "Scan triggered"}

@router.get("/market/summary")
async def market_summary():
    cached = await cache_get("scanner:all_signals")
    signals = cached.get("signals", []) if cached else []
    summary = await generate_market_summary(signals)
    breadth = {
        "strong_buy": sum(1 for s in signals if s.get("signal") == "STRONG_BUY"),
        "buy": sum(1 for s in signals if s.get("signal") == "BUY"),
        "neutral": sum(1 for s in signals if s.get("signal") == "NEUTRAL"),
        "sell": sum(1 for s in signals if s.get("signal") == "SELL"),
        "strong_sell": sum(1 for s in signals if s.get("signal") == "STRONG_SELL"),
        "total": len(signals),
    }
    return {"summary": summary, "breadth": breadth, "ts": datetime.now().isoformat()}

@router.get("/market/breadth")
async def market_breadth():
    cached = await cache_get("scanner:all_signals")
    signals = cached.get("signals", []) if cached else []
    return {
        "strong_buy": sum(1 for s in signals if s.get("signal") == "STRONG_BUY"),
        "buy": sum(1 for s in signals if s.get("signal") == "BUY"),
        "neutral": sum(1 for s in signals if s.get("signal") == "NEUTRAL"),
        "sell": sum(1 for s in signals if s.get("signal") == "SELL"),
        "strong_sell": sum(1 for s in signals if s.get("signal") == "STRONG_SELL"),
        "total": len(signals),
        "advance_decline": sum(1 for s in signals if "BUY" in s.get("signal","")) - sum(1 for s in signals if "SELL" in s.get("signal","")),
    }

@router.get("/stock/{symbol}/detail")
async def stock_detail(symbol: str, db: AsyncSession = Depends(get_db)):
    symbol = symbol.upper()
    cached = await cache_get(f"scanner:{symbol}")
    if not cached:
        raise HTTPException(status_code=404, detail="Symbol not found")
    ai_summary = await generate_stock_summary(symbol, cached)
    return {**cached, "ai_summary": ai_summary}

@router.get("/stock/{symbol}/history")
async def stock_history(symbol: str, days: int = 30, db: AsyncSession = Depends(get_db)):
    symbol = symbol.upper()
    cutoff = datetime.now() - timedelta(days=days)
    q = select(Quote).where(Quote.symbol == symbol, Quote.timestamp >= cutoff).order_by(Quote.timestamp)
    result = await db.execute(q)
    rows = result.scalars().all()
    return {"symbol": symbol, "data": [{"ts": r.timestamp.isoformat(), "price": r.ltp, "volume": r.volume} for r in rows]}

@router.get("/options/{symbol}")
async def option_chain(symbol: str):
    symbol = symbol.upper()
    cached = await cache_get(f"options:{symbol}")
    if cached:
        return cached
    data = await nse_service.fetch_option_chain(symbol)
    if not data:
        raise HTTPException(status_code=503, detail="Option chain unavailable")
    await cache_set(f"options:{symbol}", data, ttl=60)
    return data

@router.get("/watchlists")
async def list_watchlists(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Watchlist))
    return [{"id": w.id, "name": w.name, "symbols": w.symbols} for w in result.scalars()]

@router.post("/watchlists")
async def create_watchlist(payload: dict, db: AsyncSession = Depends(get_db)):
    wl = Watchlist(name=payload["name"], symbols=payload.get("symbols", []))
    db.add(wl)
    await db.commit()
    await db.refresh(wl)
    return {"id": wl.id, "name": wl.name, "symbols": wl.symbols}

@router.put("/watchlists/{wl_id}")
async def update_watchlist(wl_id: int, payload: dict, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Watchlist).where(Watchlist.id == wl_id))
    wl = result.scalar_one_or_none()
    if not wl:
        raise HTTPException(status_code=404)
    wl.symbols = payload.get("symbols", wl.symbols)
    wl.name = payload.get("name", wl.name)
    await db.commit()
    return {"id": wl.id, "name": wl.name, "symbols": wl.symbols}

@router.get("/symbols")
async def get_symbols():
    return {"symbols": FNO_SYMBOLS, "count": len(FNO_SYMBOLS)}
