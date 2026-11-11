"""Local import of lawfully obtained normalized IPO metadata; no exchange scraping."""

import math
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from scrapers.gmp.validators import normalize_name

COLUMNS = [
    "ipo_name",
    "ipo_slug",
    "open_date",
    "close_date",
    "price_band_low",
    "price_band_high",
    "lot_size",
    "listing_date",
    "exchange",
    "status",
    "source_url",
    "retrieved_at_utc",
]


def collect_ipo(path: Path | None = None) -> pd.DataFrame:
    if path is None:
        return pd.DataFrame(columns=COLUMNS)
    frame = (
        pd.read_csv(path, dtype=str, keep_default_na=False)
        if path.suffix.lower() == ".csv"
        else pd.read_json(path, dtype=False)
    )
    required = {"ipo_name", "exchange", "source_url"}
    if not required <= set(frame.columns):
        raise ValueError(f"IPO import requires {sorted(required)}")
    frame = frame.reindex(columns=COLUMNS).astype(object)
    for index, row in frame.iterrows():
        if not isinstance(row.ipo_name, str) or not normalize_name(row.ipo_name):
            raise ValueError("IPO name required")
        frame.at[index, "ipo_slug"] = normalize_name(row.ipo_name)
        if row.exchange not in ("NSE", "BSE", "NSE/BSE"):
            raise ValueError("Exchange must be NSE, BSE or NSE/BSE")
        if not isinstance(row.source_url, str) or not row.source_url.startswith("https://"):
            raise ValueError("Provenance HTTPS URL required; import does not authenticate it")
    for column in ("open_date", "close_date", "listing_date"):
        frame[column] = pd.to_datetime(
            frame[column].replace("", None), format="%Y-%m-%d", errors="raise"
        ).dt.strftime("%Y-%m-%d")
    if (
        (frame.close_date < frame.open_date) & frame.close_date.notna() & frame.open_date.notna()
    ).any():
        raise ValueError("Closing date precedes opening date")
    for column in ("price_band_low", "price_band_high", "lot_size"):
        frame[column] = pd.to_numeric(frame[column].replace("", None), errors="raise")
        if any(not math.isfinite(float(value)) or value <= 0 for value in frame[column].dropna()):
            raise ValueError("Prices and lot sizes must be positive")
    if (frame.lot_size.dropna() % 1 != 0).any() or (
        frame.price_band_low > frame.price_band_high
    ).any():
        raise ValueError("Invalid lot size or price band")
    frame["retrieved_at_utc"] = datetime.now(timezone.utc).isoformat()
    return frame.drop_duplicates(["ipo_slug", "exchange"]).reset_index(drop=True)
