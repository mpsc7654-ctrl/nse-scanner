import logging
import pandas as pd
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.models import Quote, Indicator, Signal
from app.services.nse_data import nse_service, FNO_SYMBOLS
from app.services.indicators import compute_indicators, generate_signal, IndicatorResult
from app.core.redis_client import cache_set, cache_get, publish

logger = logging.getLogger(__name__)

class ScannerService:

    async def run_full_scan(self, db: AsyncSession):
        logger.info("Starting full scan...")
        try:
            quotes = await nse_service.fetch_all_quotes()
            results = []
            for quote in quotes:
                try:
                    result = await self._process_symbol(db, quote)
                    if result:
                        results.append(result)
                except Exception as e:
                    logger.error(f"Error processing {quote.get('symbol')}: {e}")

            await cache_set(
                "scanner:all_signals",
                {"signals": results, "updated_at": datetime.now().isoformat()},
                ttl=180,
            )
            await publish("scanner:update", {
                "type": "scan_complete",
                "count": len(results),
                "ts": datetime.now().isoformat(),
            })
            logger.info(f"Scan complete: {len(results)} symbols processed")
            return results
        except Exception as e:
            logger.error(f"Full scan failed: {e}")
            return []

    async def _process_symbol(self, db: AsyncSession, quote: dict):
        symbol = quote["symbol"]
        current_price = float(quote.get("ltp", 0))
        current_volume = float(quote.get("volume", 0))

        if current_price <= 0:
            return None

        # Try cache first; fall back to yfinance
        cached_hist = await cache_get(f"hist:{symbol}")
        if cached_hist:
            try:
                df = pd.DataFrame(cached_hist)
                df.index = pd.to_datetime(df["date"])
                for col in ["Open", "High", "Low", "Close", "Volume"]:
                    df[col] = pd.to_numeric(df[col], errors="coerce")
                df.dropna(inplace=True)
            except Exception:
                df = None
        else:
            df = nse_service.fetch_historical_yf(symbol, period="1y")
            if df is not None and len(df) >= 120:
                hist_cache = df.reset_index()
                # yfinance index column may be "Date" or "Datetime"
                date_col = "Date" if "Date" in hist_cache.columns else hist_cache.columns[0]
                hist_cache = hist_cache.rename(columns={date_col: "date"})
                hist_cache["date"] = hist_cache["date"].astype(str)
                cols = [c for c in ["date","Open","High","Low","Close","Volume"] if c in hist_cache.columns]
                await cache_set(
                    f"hist:{symbol}",
                    hist_cache[cols].to_dict(orient="records"),
                    ttl=3600,
                )

        if df is None or len(df) < 120:
            logger.warning(f"Insufficient data for {symbol} ({len(df) if df is not None else 0} rows)")
            return None

        ind = compute_indicators(symbol, df)
        if ind is None:
            return None

        sig = generate_signal(symbol, ind, current_price, current_volume, df)

        await self._save_quote(db, quote)
        await self._save_indicator(db, ind)
        await self._save_signal(db, sig)

        payload = {
            "symbol": symbol,
            "price": current_price,
            "change_pct": float(quote.get("change_pct", 0)),
            "volume": current_volume,
            "signal": sig.signal_type,
            "confidence": sig.confidence,
            "entry": sig.entry,
            "stoploss": sig.stoploss,
            "target1": sig.target1,
            "target2": sig.target2,
            "risk_reward": sig.risk_reward,
            "option_strike": sig.option_strike,
            "option_type": sig.option_type,
            "ema20": ind.ema20,
            "ema100": ind.ema100,
            "macd": ind.macd,
            "macd_signal": ind.macd_signal,
            "macd_hist": ind.macd_hist,
            "rsi14": ind.rsi14,
            "atr": ind.atr,
            "vwap": ind.vwap,
            "avg_volume_20": ind.avg_volume_20,
            "support1": ind.support1,
            "support2": ind.support2,
            "resistance1": ind.resistance1,
            "resistance2": ind.resistance2,
            "prev_day_high": ind.prev_day_high,
            "prev_day_low": ind.prev_day_low,
            "week_high": ind.week_high,
            "week_low": ind.week_low,
            "reasoning": sig.reasoning,
        }
        await cache_set(f"scanner:{symbol}", payload, ttl=180)
        return payload

    async def _save_quote(self, db: AsyncSession, quote: dict):
        try:
            allowed = {"symbol","ltp","open","high","low","close","prev_close","volume","change_pct"}
            db.add(Quote(**{k: v for k, v in quote.items() if k in allowed}))
            await db.commit()
        except Exception as e:
            await db.rollback()
            logger.debug(f"Quote save skipped: {e}")

    async def _save_indicator(self, db: AsyncSession, ind: IndicatorResult):
        try:
            data = {k: v for k, v in ind.__dict__.items()}
            db.add(Indicator(**data))
            await db.commit()
        except Exception as e:
            await db.rollback()
            logger.debug(f"Indicator save skipped: {e}")

    async def _save_signal(self, db: AsyncSession, sig):
        try:
            db.add(Signal(
                symbol=sig.symbol,
                signal_type=sig.signal_type,
                confidence=sig.confidence,
                entry=sig.entry,
                stoploss=sig.stoploss,
                target1=sig.target1,
                target2=sig.target2,
                risk_reward=sig.risk_reward,
                option_strike=sig.option_strike,
                option_type=sig.option_type,
                reasoning=sig.reasoning,
                is_active=True,
            ))
            await db.commit()
        except Exception as e:
            await db.rollback()
            logger.debug(f"Signal save skipped: {e}")

scanner_service = ScannerService()
