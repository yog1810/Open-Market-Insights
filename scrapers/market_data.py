"""Free, delayed/indicative market data via Yahoo Finance (unofficial)."""
from __future__ import annotations
import logging
from datetime import datetime, timezone
import pandas as pd
import yfinance as yf

LOG = logging.getLogger(__name__)
DEFAULT_SYMBOLS = ("RELIANCE.NS", "TCS.NS", "INFY.NS", "^NSEI", "^BSESN")
COLUMNS = ["symbol", "date", "open", "high", "low", "close", "volume", "retrieved_at_utc"]


def collect_market_data(symbols: tuple[str, ...] = DEFAULT_SYMBOLS,
                        period: str = "5d") -> pd.DataFrame:
    rows = []
    for symbol in symbols:
        try:
            history = yf.Ticker(symbol).history(period=period, auto_adjust=False)
            if history.empty:
                LOG.warning("No history for %s", symbol)
                continue
            timestamp = datetime.now(timezone.utc).isoformat()
            for date, row in history.iterrows():
                rows.append({"symbol": symbol, "date": date.isoformat(),
                             "open": float(row["Open"]), "high": float(row["High"]),
                             "low": float(row["Low"]), "close": float(row["Close"]),
                             "volume": int(row["Volume"]) if pd.notna(row["Volume"]) else None,
                             "retrieved_at_utc": timestamp})
        except Exception as exc:  # third-party client raises varying exceptions
            LOG.warning("Market data unavailable for %s: %s", symbol, exc)
    return pd.DataFrame(rows, columns=COLUMNS)
