"""Unadjusted daily OHLCV from unofficial Yahoo Finance; may be delayed/revised."""

from __future__ import annotations

import logging
import math
import re
import time
from datetime import datetime, timezone

import pandas as pd
import yfinance as yf

LOG = logging.getLogger(__name__)
DEFAULT_SYMBOLS = ("RELIANCE.NS", "TCS.NS", "INFY.NS", "RELIANCE.BO", "^NSEI", "^BSESN")
COLUMNS = [
    "symbol",
    "date",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "source",
    "price_basis",
    "retrieved_at_utc",
]
INDICATORS = ["sma_20", "sma_50", "rsi_14", "daily_change_pct"]


def normalize_history(history: pd.DataFrame, symbol: str, indicators=False) -> pd.DataFrame:
    rows, validation_errors = [], []
    if isinstance(history.columns, pd.MultiIndex):
        # Accept both (field, ticker) and (ticker, field) layouts.
        for level in range(history.columns.nlevels):
            if symbol in history.columns.get_level_values(level):
                history = history.xs(symbol, axis=1, level=level)
                break
    if not history.empty and not {"Open", "High", "Low", "Close", "Volume"} <= set(history.columns):
        raise ValueError(f"{symbol}: missing OHLCV columns")
    for date, row in history.iterrows():
        try:
            prices = [float(row[c]) for c in ("Open", "High", "Low", "Close")]
            o, h, low, c = prices
            if (
                not all(math.isfinite(p) and p > 0 for p in prices)
                or not low <= min(o, c) <= max(o, c) <= h
            ):
                raise ValueError("Invalid OHLC range or missing price")
            volume = row["Volume"]
            if pd.notna(volume) and (
                not math.isfinite(float(volume)) or float(volume) < 0 or float(volume) % 1
            ):
                raise ValueError("Invalid volume")
            stamp = pd.Timestamp(date)
            if pd.isna(stamp):
                raise ValueError("Missing date")
            # Naive daily Indian equity bars are exchange-local midnight.
            stamp = stamp.tz_localize("Asia/Kolkata") if stamp.tzinfo is None else stamp
            rows.append(
                dict(
                    symbol=symbol,
                    date=stamp.tz_convert("UTC").isoformat(),
                    open=o,
                    high=h,
                    low=low,
                    close=c,
                    volume=int(volume) if pd.notna(volume) else None,
                    source="Yahoo Finance via yfinance",
                    price_basis="unadjusted daily; delayed/indicative",
                    retrieved_at_utc=datetime.now(timezone.utc).isoformat(),
                )
            )
        except (ValueError, TypeError, OverflowError) as exc:
            validation_errors.append(f"{symbol} {date}: {exc}")
            LOG.warning("invalid_price_row symbol=%s date=%s error=%s", symbol, date, exc)
    frame = (
        pd.DataFrame(rows, columns=COLUMNS)
        .drop_duplicates(["symbol", "date"])
        .sort_values("date")
        .reset_index(drop=True)
    )
    if indicators:
        close = frame["close"].astype(float)
        frame["sma_20"] = close.rolling(20, min_periods=20).mean()
        frame["sma_50"] = close.rolling(50, min_periods=50).mean()
        delta = close.diff()
        # Wilder RSI: seed with arithmetic mean of first 14 changes.
        gain, loss = delta.clip(lower=0), -delta.clip(upper=0)
        rsi = pd.Series(float("nan"), index=frame.index)
        if len(frame) > 14:
            avg_gain, avg_loss = gain.iloc[1:15].mean(), loss.iloc[1:15].mean()
            for i in range(14, len(frame)):
                if i > 14:
                    avg_gain = (avg_gain * 13 + gain.iloc[i]) / 14
                    avg_loss = (avg_loss * 13 + loss.iloc[i]) / 14
                rsi.iloc[i] = (
                    50
                    if avg_gain == avg_loss == 0
                    else (100 if avg_loss == 0 else 100 - 100 / (1 + avg_gain / avg_loss))
                )
        frame["rsi_14"] = rsi
        frame["daily_change_pct"] = close.pct_change(fill_method=None) * 100
    frame.attrs["validation_errors"] = validation_errors
    return frame


def collect_market_data(
    symbols=DEFAULT_SYMBOLS, period="5d", *, attempts=3, indicators=False, sleep=time.sleep
) -> pd.DataFrame:
    if period not in {"1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"}:
        raise ValueError("Unsupported history period")
    if not 1 <= attempts <= 5:
        raise ValueError("attempts must be 1..5")
    frames, errors = [], []
    for symbol in dict.fromkeys(symbols):
        if not re.fullmatch(r"(?:[A-Z0-9&_.-]+\.(?:NS|BO)|\^[A-Z0-9]+)", symbol):
            errors.append(f"{symbol}: unsupported ticker format")
            continue
        for attempt in range(attempts):
            try:
                history = yf.Ticker(symbol).history(
                    period=period, interval="1d", auto_adjust=False, raise_errors=True, timeout=20
                )
                frame = normalize_history(history, symbol, indicators)
                if frame.empty:
                    raise ValueError("No valid price history returned")
                errors.extend(frame.attrs.get("validation_errors", []))
                frames.append(frame)
                break
            except Exception as exc:
                # yfinance exception classes vary by release. Never retry a rate limit
                # without a known Retry-After; stop this ticker instead.
                if "ratelimit" in type(exc).__name__.lower() or "429" in str(exc):
                    errors.append(f"{symbol}: rate limited; stopped")
                    break
                if attempt + 1 == attempts:
                    errors.append(f"{symbol}: {exc}")
                else:
                    sleep(2**attempt)
        sleep(1)
    for error in errors:
        LOG.warning("market_source_failed error=%s", error)
    result = (
        pd.concat(frames, ignore_index=True)
        if frames
        else pd.DataFrame(columns=COLUMNS + (INDICATORS if indicators else []))
    )
    result.attrs["errors"] = errors
    return result
