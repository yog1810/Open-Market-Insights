"""Opt-in personal-use smoke checks. Never enables restricted GMP/exchange sources.

Run from repository root: python scripts/verify_live.py --personal-use
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scrapers.http import PoliteClient  # noqa: E402
from scrapers.market_data import collect_market_data  # noqa: E402
from scrapers.news_insights import CANDIDATE_FEEDS, parse_news  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--personal-use", action="store_true", required=True)
    args = parser.parse_args()
    if not args.personal_use:
        return 2
    report = {"checked_at_utc": datetime.now(timezone.utc).isoformat(), "sources": []}
    client = PoliteClient(attempts=1)
    try:
        for name, url in CANDIDATE_FEEDS.items():
            try:
                rows = parse_news(client.get(url).content, name)
                report["sources"].append(
                    dict(source=name, status="passed" if rows else "empty", rows=len(rows))
                )
            except Exception as exc:
                report["sources"].append(dict(source=name, status="unverified", error=str(exc)))
    finally:
        client.close()
    prices = collect_market_data(("RELIANCE.NS", "RELIANCE.BO", "^NSEI", "^BSESN"), attempts=1)
    from scrapers.storage import save

    save(prices, "live_prices", Path("data/stocks"))
    report["sources"].append(
        dict(
            source="yfinance",
            status="passed" if len(prices) and not prices.attrs.get("errors") else "unverified",
            rows=len(prices),
            errors=prices.attrs.get("errors", []),
        )
    )
    path = Path("data/logs/live_verification.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if all(row["status"] == "passed" for row in report["sources"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
