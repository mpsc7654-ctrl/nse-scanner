import httpx
import asyncio
import logging
from datetime import datetime, date
from typing import Optional
import yfinance as yf
import pandas as pd

logger = logging.getLogger(__name__)

NSE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Referer": "https://www.nseindia.com/",
    "Accept-Language": "en-US,en;q=0.9",
}

# Full F&O stock list (top 50 liquid stocks)
FNO_SYMBOLS = [
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "HINDUNILVR",
    "SBIN", "BHARTIARTL", "KOTAKBANK", "ITC", "LT", "HCLTECH", "AXISBANK",
    "ASIANPAINT", "MARUTI", "BAJFINANCE", "ULTRACEMCO", "NESTLEIND", "TITAN",
    "WIPRO", "SUNPHARMA", "BAJAJFINSV", "ONGC", "NTPC", "POWERGRID",
    "TATAMOTORS", "M&M", "TECHM", "ADANIENT", "JSWSTEEL", "TATASTEEL",
    "INDUSINDBK", "HINDALCO", "COALINDIA", "BPCL", "DRREDDY", "CIPLA",
    "DIVISLAB", "APOLLOHOSP", "EICHERMOT", "HEROMOTOCO", "GRASIM",
    "BAJAJ-AUTO", "BRITANNIA", "SBILIFE", "HDFC", "PIDILITIND", "DMART",
    "ADANIPORTS", "GODREJCP"
]

class NSEDataService:
    def __init__(self):
        self._session: Optional[httpx.AsyncClient] = None
        self._cookies_initialized = False

    async def get_session(self) -> httpx.AsyncClient:
        if self._session is None or self._session.is_closed:
            self._session = httpx.AsyncClient(
                headers=NSE_HEADERS,
                timeout=httpx.Timeout(30.0),
                follow_redirects=True,
            )
            await self._init_cookies()
        return self._session

    async def _init_cookies(self):
        try:
            session = self._session
            await session.get("https://www.nseindia.com/")
            await session.get("https://www.nseindia.com/market-data/live-equity-market")
            self._cookies_initialized = True
        except Exception as e:
            logger.warning(f"Cookie init failed: {e}")

    async def fetch_quote(self, symbol: str) -> dict | None:
        try:
            session = await self.get_session()
            url = f"https://www.nseindia.com/api/quote-equity?symbol={symbol}"
            resp = await session.get(url)
            if resp.status_code == 200:
                data = resp.json()
                pd_data = data.get("priceInfo", {})
                return {
                    "symbol": symbol,
                    "ltp": pd_data.get("lastPrice", 0),
                    "open": pd_data.get("open", 0),
                    "high": pd_data.get("intraDayHighLow", {}).get("max", 0),
                    "low": pd_data.get("intraDayHighLow", {}).get("min", 0),
                    "close": pd_data.get("close", 0),
                    "prev_close": pd_data.get("previousClose", 0),
                    "volume": data.get("marketDeptOrderBook", {}).get("tradeInfo", {}).get("totalTradedVolume", 0),
                    "change_pct": pd_data.get("pChange", 0),
                }
        except Exception as e:
            logger.error(f"NSE quote fetch failed for {symbol}: {e}")
        return None

    async def fetch_option_chain(self, symbol: str) -> dict | None:
        try:
            session = await self.get_session()
            url = f"https://www.nseindia.com/api/option-chain-equities?symbol={symbol}"
            resp = await session.get(url)
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            logger.error(f"Option chain fetch failed for {symbol}: {e}")
        return None

    async def fetch_all_quotes(self) -> list[dict]:
        tasks = [self.fetch_quote(sym) for sym in FNO_SYMBOLS]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r for r in results if isinstance(r, dict) and r]

    def fetch_historical_yf(self, symbol: str, period: str = "1y") -> pd.DataFrame | None:
        """Fallback: fetch historical data from Yahoo Finance"""
        try:
            ticker = yf.Ticker(f"{symbol}.NS")
            df = ticker.history(period=period)
            if df.empty:
                return None
            df.index = df.index.tz_localize(None)
            return df
        except Exception as e:
            logger.error(f"YF fetch failed for {symbol}: {e}")
            return None

nse_service = NSEDataService()
