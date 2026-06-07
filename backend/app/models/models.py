from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, JSON, Text, Index
from sqlalchemy.sql import func
from app.core.database import Base

class Stock(Base):
    __tablename__ = "stocks"
    symbol     = Column(String(20), primary_key=True)
    name       = Column(String(100))
    lot_size   = Column(Integer, default=1)
    is_active  = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Quote(Base):
    __tablename__ = "quotes"
    id         = Column(Integer, primary_key=True, autoincrement=True)
    symbol     = Column(String(20), nullable=False)
    ltp        = Column(Float)
    open       = Column(Float)
    high       = Column(Float)
    low        = Column(Float)
    close      = Column(Float)
    prev_close = Column(Float)
    volume     = Column(Float)
    oi         = Column(Float)
    change_pct = Column(Float)
    timestamp  = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (Index("ix_quotes_symbol_ts", "symbol", "timestamp"),)

class Candle(Base):
    __tablename__ = "candles"
    id        = Column(Integer, primary_key=True, autoincrement=True)
    symbol    = Column(String(20), nullable=False)
    interval  = Column(String(10), default="1d")
    open      = Column(Float)
    high      = Column(Float)
    low       = Column(Float)
    close     = Column(Float)
    volume    = Column(Float)
    timestamp = Column(DateTime(timezone=True))
    __table_args__ = (Index("ix_candles_symbol_interval_ts", "symbol", "interval", "timestamp"),)

class Indicator(Base):
    __tablename__ = "indicators"
    id            = Column(Integer, primary_key=True, autoincrement=True)
    symbol        = Column(String(20), nullable=False)
    ema20         = Column(Float)
    ema100        = Column(Float)
    macd          = Column(Float)
    macd_signal   = Column(Float)
    macd_hist     = Column(Float)
    rsi14         = Column(Float)
    atr           = Column(Float)
    vwap          = Column(Float)
    avg_volume_20 = Column(Float)
    support1      = Column(Float)
    support2      = Column(Float)
    resistance1   = Column(Float)
    resistance2   = Column(Float)
    prev_day_high = Column(Float)
    prev_day_low  = Column(Float)
    week_high     = Column(Float)
    week_low      = Column(Float)
    timestamp     = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (Index("ix_indicators_symbol_ts", "symbol", "timestamp"),)

class Signal(Base):
    __tablename__ = "signals"
    id            = Column(Integer, primary_key=True, autoincrement=True)
    symbol        = Column(String(20), nullable=False)
    signal_type   = Column(String(20))
    confidence    = Column(Float)
    entry         = Column(Float)
    stoploss      = Column(Float)
    target1       = Column(Float)
    target2       = Column(Float)
    risk_reward   = Column(Float)
    option_strike = Column(Float)
    option_type   = Column(String(2))
    reasoning     = Column(Text)
    is_active     = Column(Boolean, default=True)
    timestamp     = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (Index("ix_signals_symbol_ts", "symbol", "timestamp"),)

class Watchlist(Base):
    __tablename__ = "watchlists"
    id         = Column(Integer, primary_key=True, autoincrement=True)
    name       = Column(String(100), nullable=False)
    symbols    = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
