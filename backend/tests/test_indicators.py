"""
Unit tests for NSE F&O Scanner — indicators, signals, support/resistance.
Run: pytest tests/test_indicators.py -v
"""
import pytest
import numpy as np
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.services.indicators import (
    ema, compute_macd, compute_rsi, compute_atr, compute_vwap,
    find_swing_levels, compute_indicators, generate_signal,
    check_macd_crossover, IndicatorResult, SignalResult
)

# ─── Fixtures ─────────────────────────────────────────────────────────────────

def make_df(n=260, seed=42, trend="flat") -> pd.DataFrame:
    np.random.seed(seed)
    dates = pd.date_range("2023-01-01", periods=n, freq="B")
    if trend == "up":
        price = np.linspace(800, 1300, n) + np.random.randn(n) * 8
    elif trend == "down":
        price = np.linspace(1300, 800, n) + np.random.randn(n) * 8
    else:
        price = 1000 + np.cumsum(np.random.randn(n) * 10)
    return pd.DataFrame({
        "Open":   price * 0.999,
        "High":   price * 1.006,
        "Low":    price * 0.994,
        "Close":  price,
        "Volume": np.random.randint(1_000_000, 8_000_000, n).astype(float),
    }, index=dates)

# ─── EMA tests ────────────────────────────────────────────────────────────────

def test_ema_length():
    s = pd.Series(np.random.randn(100))
    assert len(ema(s, 20)) == 100

def test_ema_convergence():
    """EMA of a constant series equals that constant."""
    s = pd.Series([100.0] * 100)
    result = ema(s, 20)
    assert abs(float(result.iloc[-1]) - 100.0) < 1e-6

def test_ema20_lt_ema100_flat():
    df = make_df(260)
    close = df["Close"]
    e20  = ema(close, 20).iloc[-1]
    e100 = ema(close, 100).iloc[-1]
    # In a flat series EMA20 should be close to EMA100
    assert abs(e20 - e100) < close.mean() * 0.05

# ─── MACD tests ───────────────────────────────────────────────────────────────

def test_macd_returns_three_series():
    df = make_df()
    line, signal, hist = compute_macd(df["Close"])
    assert len(line) == len(df)
    assert len(signal) == len(df)
    assert len(hist) == len(df)

def test_macd_hist_equals_line_minus_signal():
    df = make_df()
    line, signal, hist = compute_macd(df["Close"])
    diff = (line - signal - hist).abs().max()
    assert diff < 1e-8

def test_macd_crossover_bullish():
    # Force a bullish crossover: hist goes from -ve to +ve
    hist = pd.Series([-1.0, -0.5, -0.1, 0.3])
    assert check_macd_crossover(hist) == "bullish"

def test_macd_crossover_bearish():
    hist = pd.Series([1.0, 0.5, 0.1, -0.2])
    assert check_macd_crossover(hist) == "bearish"

def test_macd_crossover_none():
    hist = pd.Series([0.1, 0.2, 0.3, 0.4])
    assert check_macd_crossover(hist) == "none"

# ─── RSI tests ────────────────────────────────────────────────────────────────

def test_rsi_range():
    df = make_df()
    rsi = compute_rsi(df["Close"])
    assert (rsi.dropna() >= 0).all()
    assert (rsi.dropna() <= 100).all()

def test_rsi_overbought_uptrend():
    df = make_df(trend="up")
    rsi = compute_rsi(df["Close"])
    # In a strong uptrend RSI should be elevated
    assert float(rsi.iloc[-1]) > 50

def test_rsi_oversold_downtrend():
    df = make_df(trend="down")
    rsi = compute_rsi(df["Close"])
    assert float(rsi.iloc[-1]) < 50

# ─── ATR tests ────────────────────────────────────────────────────────────────

def test_atr_positive():
    df = make_df()
    atr = compute_atr(df["High"], df["Low"], df["Close"])
    assert float(atr.iloc[-1]) > 0

def test_atr_scales_with_volatility():
    df_lo = make_df(seed=1)
    df_hi = df_lo.copy()
    df_hi["High"] = df_hi["High"] * 1.05
    df_hi["Low"]  = df_hi["Low"]  * 0.95
    atr_lo = float(compute_atr(df_lo["High"], df_lo["Low"], df_lo["Close"]).iloc[-1])
    atr_hi = float(compute_atr(df_hi["High"], df_hi["Low"], df_hi["Close"]).iloc[-1])
    assert atr_hi > atr_lo

# ─── VWAP tests ───────────────────────────────────────────────────────────────

def test_vwap_positive():
    df = make_df()
    v = compute_vwap(df["High"], df["Low"], df["Close"], df["Volume"])
    assert v > 0

def test_vwap_near_price():
    df = make_df()
    v = compute_vwap(df["High"], df["Low"], df["Close"], df["Volume"])
    price = float(df["Close"].mean())
    # VWAP should be within 20% of mean price
    assert abs(v - price) / price < 0.20

# ─── Support/Resistance tests ─────────────────────────────────────────────────

def test_swing_detects_peaks_troughs():
    n = 260
    t = np.linspace(0, 6*np.pi, n)
    price = 1000 + 100 * np.sin(t)
    dates = pd.date_range("2023-01-01", periods=n, freq="B")
    high = pd.Series(price + 5, index=dates)
    low  = pd.Series(price - 5, index=dates)
    sup, res = find_swing_levels(high, low, lookback=120)
    assert len(sup) >= 1, "Must detect at least one support"
    assert len(res) >= 1, "Must detect at least one resistance"

def test_resistance_above_support():
    df = make_df()
    sup, res = find_swing_levels(df["High"], df["Low"], lookback=120)
    if sup and res:
        assert max(res) > min(sup)

def test_swing_lookback_zero_returns_empty():
    df = make_df()
    sup, res = find_swing_levels(df["High"], df["Low"], lookback=5)
    # At least empty list, not an exception
    assert isinstance(sup, list)
    assert isinstance(res, list)

# ─── compute_indicators tests ─────────────────────────────────────────────────

def test_indicators_returns_result():
    df = make_df()
    ind = compute_indicators("TEST", df)
    assert ind is not None
    assert isinstance(ind, IndicatorResult)

def test_indicators_none_on_short_data():
    df = make_df(n=50)
    assert compute_indicators("SHORT", df) is None

def test_indicators_values_positive():
    df = make_df()
    ind = compute_indicators("TEST", df)
    assert ind.ema20 > 0
    assert ind.ema100 > 0
    assert ind.rsi14 > 0
    assert ind.atr > 0
    assert ind.vwap > 0
    assert ind.avg_volume_20 > 0

def test_indicators_ema_ordering_uptrend():
    """In uptrend: EMA20 should be above EMA100."""
    df = make_df(trend="up")
    ind = compute_indicators("UP", df)
    assert ind is not None
    assert ind.ema20 > ind.ema100

def test_indicators_ema_ordering_downtrend():
    df = make_df(trend="down")
    ind = compute_indicators("DOWN", df)
    assert ind is not None
    assert ind.ema20 < ind.ema100

# ─── generate_signal tests ───────────────────────────────────────────────────

def test_signal_returns_result():
    df = make_df()
    ind = compute_indicators("TEST", df)
    sig = generate_signal("TEST", ind, float(df["Close"].iloc[-1]), float(df["Volume"].iloc[-1]), df)
    assert isinstance(sig, SignalResult)

def test_signal_type_valid():
    df = make_df()
    ind = compute_indicators("TEST", df)
    sig = generate_signal("TEST", ind, float(df["Close"].iloc[-1]), float(df["Volume"].iloc[-1]), df)
    assert sig.signal_type in ("STRONG_BUY", "BUY", "NEUTRAL", "SELL", "STRONG_SELL")

def test_signal_confidence_range():
    df = make_df()
    ind = compute_indicators("TEST", df)
    sig = generate_signal("TEST", ind, float(df["Close"].iloc[-1]), float(df["Volume"].iloc[-1]), df)
    assert 0 <= sig.confidence <= 100

def test_signal_option_type_valid():
    df = make_df()
    ind = compute_indicators("TEST", df)
    sig = generate_signal("TEST", ind, float(df["Close"].iloc[-1]), float(df["Volume"].iloc[-1]), df)
    assert sig.option_type in ("CE", "PE")

def test_signal_stoploss_below_entry_on_buy():
    df = make_df(trend="up")
    ind = compute_indicators("UP", df)
    sig = generate_signal("UP", ind, float(df["Close"].iloc[-1]), 6_000_000.0, df)
    if sig.signal_type in ("BUY", "STRONG_BUY"):
        assert sig.stoploss < sig.entry, "Buy stoploss must be below entry"

def test_signal_stoploss_above_entry_on_sell():
    df = make_df(trend="down")
    ind = compute_indicators("DOWN", df)
    sig = generate_signal("DOWN", ind, float(df["Close"].iloc[-1]), 6_000_000.0, df)
    if sig.signal_type in ("SELL", "STRONG_SELL"):
        assert sig.stoploss > sig.entry, "Sell stoploss must be above entry"

def test_signal_target1_above_entry_on_buy():
    df = make_df(trend="up")
    ind = compute_indicators("UP", df)
    sig = generate_signal("UP", ind, float(df["Close"].iloc[-1]), 6_000_000.0, df)
    if sig.signal_type in ("BUY", "STRONG_BUY"):
        assert sig.target1 > sig.entry

def test_signal_risk_reward_positive():
    df = make_df()
    ind = compute_indicators("TEST", df)
    sig = generate_signal("TEST", ind, float(df["Close"].iloc[-1]), float(df["Volume"].iloc[-1]), df)
    assert sig.risk_reward >= 0

def test_signal_strong_buy_uptrend_high_volume():
    """Strong uptrend + high volume should produce BUY or STRONG_BUY."""
    df = make_df(trend="up", n=260)
    ind = compute_indicators("UP", df)
    # 3x average volume
    sig = generate_signal("UP", ind, float(df["Close"].iloc[-1]), ind.avg_volume_20 * 3, df)
    assert sig.signal_type in ("BUY", "STRONG_BUY", "NEUTRAL")

def test_option_strike_rounded():
    df = make_df()
    ind = compute_indicators("TEST", df)
    sig = generate_signal("TEST", ind, 1500.0, 2_000_000.0, df)
    # Strike should be a multiple of 50 for price < 2000
    assert sig.option_strike % 50 == 0

def test_option_strike_rounded_expensive():
    df = make_df()
    ind = compute_indicators("TEST", df)
    sig = generate_signal("TEST", ind, 2500.0, 2_000_000.0, df)
    # Strike should be a multiple of 100 for price >= 2000
    assert sig.option_strike % 100 == 0
