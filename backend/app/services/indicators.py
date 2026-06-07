"""
Pure deterministic technical indicator engine.
No AI. All math. Fast. Accurate.
"""
import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import Optional

@dataclass
class IndicatorResult:
    symbol: str
    ema20: float
    ema100: float
    macd: float
    macd_signal: float
    macd_hist: float
    rsi14: float
    atr: float
    vwap: float
    avg_volume_20: float
    support1: float
    support2: float
    resistance1: float
    resistance2: float
    prev_day_high: float
    prev_day_low: float
    week_high: float
    week_low: float

@dataclass
class SignalResult:
    symbol: str
    signal_type: str
    confidence: float
    entry: float
    stoploss: float
    target1: float
    target2: float
    risk_reward: float
    option_strike: float
    option_type: str
    reasoning: str

# ─── Core math ────────────────────────────────────────────────────────────────

def ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()

def compute_macd(close: pd.Series):
    fast   = ema(close, 12)
    slow   = ema(close, 26)
    line   = fast - slow
    signal = ema(line, 9)
    hist   = line - signal
    return line, signal, hist

def compute_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta    = close.diff()
    gain     = delta.clip(lower=0)
    loss     = (-delta).clip(lower=0)
    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
    rs       = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

def compute_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    hl  = high - low
    hc  = (high - close.shift()).abs()
    lc  = (low  - close.shift()).abs()
    tr  = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    return tr.ewm(alpha=1/period, adjust=False).mean()

def compute_vwap(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> float:
    typical  = (high + low + close) / 3
    cum_vol  = volume.cumsum()
    if cum_vol.iloc[-1] == 0:
        return float(close.iloc[-1])
    vwap = (typical * volume).cumsum() / cum_vol
    return float(vwap.iloc[-1])

# ─── Support / Resistance ─────────────────────────────────────────────────────

def find_swing_levels(high: pd.Series, low: pd.Series, lookback: int = 60):
    """
    Scan the last `lookback` bars for local swing highs (resistance)
    and swing lows (support).  Uses a 2-bar pivot window on each side.
    """
    h = high.values
    l = low.values
    n = len(h)

    # Scan from (n-lookback) to (n-3) so we always have 2 bars on each side
    start = max(2, n - lookback)
    end   = n - 2

    supports    = []
    resistances = []

    for idx in range(start, end):
        if (h[idx] > h[idx-1] and h[idx] > h[idx-2] and
                h[idx] > h[idx+1] and h[idx] > h[idx+2]):
            resistances.append(float(h[idx]))
        if (l[idx] < l[idx-1] and l[idx] < l[idx-2] and
                l[idx] < l[idx+1] and l[idx] < l[idx+2]):
            supports.append(float(l[idx]))

    return sorted(supports), sorted(resistances)

# ─── Main indicator computation ───────────────────────────────────────────────

def compute_indicators(symbol: str, df: pd.DataFrame) -> Optional[IndicatorResult]:
    if df is None or len(df) < 120:
        return None

    close  = df["Close"].astype(float)
    high   = df["High"].astype(float)
    low    = df["Low"].astype(float)
    volume = df["Volume"].astype(float)

    ema20_s  = ema(close, 20)
    ema100_s = ema(close, 100)
    macd_line, macd_sig, macd_hist = compute_macd(close)
    rsi_s    = compute_rsi(close)
    atr_s    = compute_atr(high, low, close)
    vwap_v   = compute_vwap(high, low, close, volume)

    avg_vol     = float(volume.iloc[-20:].mean())
    supports, resistances = find_swing_levels(high, low, lookback=120)

    prev_high = float(high.iloc[-2]) if len(df) > 1 else float(high.iloc[-1])
    prev_low  = float(low.iloc[-2])  if len(df) > 1 else float(low.iloc[-1])
    week_high = float(high.iloc[-5:].max())
    week_low  = float(low.iloc[-5:].min())

    return IndicatorResult(
        symbol       = symbol,
        ema20        = round(float(ema20_s.iloc[-1]),  2),
        ema100       = round(float(ema100_s.iloc[-1]), 2),
        macd         = round(float(macd_line.iloc[-1]), 4),
        macd_signal  = round(float(macd_sig.iloc[-1]),  4),
        macd_hist    = round(float(macd_hist.iloc[-1]), 4),
        rsi14        = round(float(rsi_s.iloc[-1]),     2),
        atr          = round(float(atr_s.iloc[-1]),     2),
        vwap         = round(vwap_v, 2),
        avg_volume_20= round(avg_vol, 0),
        support1     = round(supports[-1],  2) if len(supports)    >= 1 else 0.0,
        support2     = round(supports[-2],  2) if len(supports)    >= 2 else 0.0,
        resistance1  = round(resistances[-1], 2) if len(resistances) >= 1 else 0.0,
        resistance2  = round(resistances[-2], 2) if len(resistances) >= 2 else 0.0,
        prev_day_high= round(prev_high, 2),
        prev_day_low = round(prev_low,  2),
        week_high    = round(week_high, 2),
        week_low     = round(week_low,  2),
    )

# ─── MACD crossover detector ─────────────────────────────────────────────────

def check_macd_crossover(hist: pd.Series, lookback: int = 3) -> str:
    if len(hist) < lookback + 1:
        return "none"
    window = hist.iloc[-(lookback+1):]
    prev   = window.iloc[:-1]
    curr   = float(window.iloc[-1])
    if any(v < 0 for v in prev) and curr > 0:
        return "bullish"
    if any(v > 0 for v in prev) and curr < 0:
        return "bearish"
    return "none"

# ─── Signal generator ────────────────────────────────────────────────────────

def generate_signal(
    symbol: str,
    ind: IndicatorResult,
    current_price: float,
    current_volume: float,
    df: pd.DataFrame,
) -> SignalResult:
    score   = 0.0
    reasons = []

    close = df["Close"].astype(float)
    _, _, hist_series = compute_macd(close)

    # 1. EMA100 trend (+/-2)
    if ind.ema100 > 0:
        gap = abs(current_price - ind.ema100) / ind.ema100 * 100
        if current_price > ind.ema100:
            score += 2
            reasons.append(f"Price above EMA100 +{gap:.1f}%")
        else:
            score -= 2
            reasons.append(f"Price below EMA100 -{gap:.1f}%")

    # 2. MACD crossover (+/-3) or momentum (+/-1)
    crossover = check_macd_crossover(hist_series)
    if crossover == "bullish":
        score += 3
        reasons.append("MACD bullish crossover")
    elif crossover == "bearish":
        score -= 3
        reasons.append("MACD bearish crossover")
    elif ind.macd > ind.macd_signal:
        score += 1
        reasons.append("MACD above signal")
    elif ind.macd < ind.macd_signal:
        score -= 1
        reasons.append("MACD below signal")

    # 3. Volume confirmation (+/-2)
    if ind.avg_volume_20 > 0 and current_volume > 1.5 * ind.avg_volume_20:
        mult = current_volume / ind.avg_volume_20
        reasons.append(f"High volume {mult:.1f}x avg")
        score += 2 if score > 0 else -2

    # 4. Support / resistance breakout (+/-2)
    if ind.resistance1 > 0 and current_price > ind.resistance1:
        score += 2
        reasons.append(f"Above resistance ₹{ind.resistance1}")
    elif ind.support1 > 0 and current_price < ind.support1:
        score -= 2
        reasons.append(f"Below support ₹{ind.support1}")

    # 5. RSI extremes (+/-1)
    if ind.rsi14 > 70:
        score -= 1
        reasons.append(f"RSI overbought {ind.rsi14:.1f}")
    elif ind.rsi14 < 30:
        score += 1
        reasons.append(f"RSI oversold {ind.rsi14:.1f}")

    # 6. EMA alignment (+/-1)
    if current_price > ind.ema20 and ind.ema20 > ind.ema100:
        score += 1
        reasons.append("EMA alignment bullish")
    elif current_price < ind.ema20 and ind.ema20 < ind.ema100:
        score -= 1
        reasons.append("EMA alignment bearish")

    # ATR-based trade levels
    atr = ind.atr if ind.atr > 0 else current_price * 0.01

    if score >= 7:
        signal_type = "STRONG_BUY"
        confidence  = min(95.0, 60 + score * 5)
        entry     = round(current_price, 2)
        stoploss  = round(current_price - 2.0 * atr, 2)
        target1   = round(current_price + 1.5 * atr, 2)
        target2   = round(current_price + 3.0 * atr, 2)
        option_type = "CE"
    elif score >= 4:
        signal_type = "BUY"
        confidence  = min(75.0, 40 + score * 5)
        entry     = round(current_price, 2)
        stoploss  = round(current_price - 1.5 * atr, 2)
        target1   = round(current_price + 1.2 * atr, 2)
        target2   = round(current_price + 2.0 * atr, 2)
        option_type = "CE"
    elif score <= -7:
        signal_type = "STRONG_SELL"
        confidence  = min(95.0, 60 + abs(score) * 5)
        entry     = round(current_price, 2)
        stoploss  = round(current_price + 2.0 * atr, 2)
        target1   = round(current_price - 1.5 * atr, 2)
        target2   = round(current_price - 3.0 * atr, 2)
        option_type = "PE"
    elif score <= -4:
        signal_type = "SELL"
        confidence  = min(75.0, 40 + abs(score) * 5)
        entry     = round(current_price, 2)
        stoploss  = round(current_price + 1.5 * atr, 2)
        target1   = round(current_price - 1.2 * atr, 2)
        target2   = round(current_price - 2.0 * atr, 2)
        option_type = "PE"
    else:
        signal_type = "NEUTRAL"
        confidence  = 50.0
        entry     = round(current_price, 2)
        stoploss  = round(current_price - atr, 2)
        target1   = round(current_price + atr, 2)
        target2   = round(current_price + 2 * atr, 2)
        option_type = "CE" if score >= 0 else "PE"

    risk   = abs(entry - stoploss)
    reward = abs(target1 - entry)
    rr     = round(reward / risk, 2) if risk > 0 else 0.0

    step           = 50 if current_price < 2000 else 100
    option_strike  = round(current_price / step) * step

    return SignalResult(
        symbol        = symbol,
        signal_type   = signal_type,
        confidence    = round(float(confidence), 1),
        entry         = entry,
        stoploss      = stoploss,
        target1       = target1,
        target2       = target2,
        risk_reward   = rr,
        option_strike = float(option_strike),
        option_type   = option_type,
        reasoning     = " | ".join(reasons) if reasons else "No clear signal",
    )
