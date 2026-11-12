"""Beginner CLI; isolated collectors with machine-readable run status."""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import pandas as pd

from scrapers.gmp import GMPSource, collect_gmp
from scrapers.gmp.investorgain import SOURCE as INVESTORGAIN
from scrapers.gmp.iporeports import SOURCE as IPOREPORTS
from scrapers.gmp.ipowatch import SOURCE as IPOWATCH
from scrapers.ipo_market import collect_ipo_market, ipo_calendar
from scrapers.ipo_metadata import collect_ipo
from scrapers.market_data import DEFAULT_SYMBOLS, collect_market_data
from scrapers.news_insights import FEEDS, collect_news
from scrapers.registry import update_registry
from scrapers.storage import save

LOG = logging.getLogger("open_market_insights")


def load_gmp_config(path: Path) -> tuple[GMPSource, ...]:
    config = json.loads(path.read_text(encoding="utf-8"))
    sources = []
    for item in config["sources"]:
        if not item["url"].startswith("https://"):
            raise ValueError("GMP source URLs must use HTTPS")
        fields = set(GMPSource.__dataclass_fields__)
        values = {k: v for k, v in item.items() if k in fields}
        if "expected_headers" in values:
            values["expected_headers"] = tuple(values["expected_headers"])
        sources.append(GMPSource(**values))
    return tuple(sources)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Indian market research toolkit. No real-time quotes or advice."
    )
    group = parser.add_mutually_exclusive_group()
    for flag in ("all", "gmp", "stocks", "news", "ipo"):
        group.add_argument("--" + flag, action="store_true")
    parser.add_argument("--symbols", nargs="+", default=list(DEFAULT_SYMBOLS))
    parser.add_argument("--period", default="5d")
    parser.add_argument("--source", help="GMP configured source name, or RSS publisher name")
    parser.add_argument("--gmp-config", type=Path)
    parser.add_argument(
        "--ipo-file", type=Path, help="Lawfully obtained normalized CSV/JSON metadata"
    )
    parser.add_argument("--output", type=Path, default=Path("data"))
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--snapshot", action="store_true")
    parser.add_argument("--indicators", action="store_true")
    parser.add_argument("--fallback-only", action="store_true")
    parser.add_argument("--limit", type=int, default=30, help="Maximum news records per publisher")
    parser.add_argument("--keywords", nargs="*", default=[])
    parser.add_argument("--acknowledge-rss-terms", action="store_true")
    args = parser.parse_args(argv)
    if args.limit < 0:
        parser.error("--limit must be >= 0")
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    selected = args.all or not any((args.gmp, args.stocks, args.news, args.ipo))
    tasks = []
    if selected or args.gmp:

        def gmp():
            sources = (
                load_gmp_config(args.gmp_config)
                if args.gmp_config
                else (IPOREPORTS, INVESTORGAIN, IPOWATCH)
            )
            if args.source:
                sources = tuple(s for s in sources if s.name.casefold() == args.source.casefold())
                if not sources:
                    raise ValueError("Unknown GMP source; configure a public source")
            return collect_gmp(sources, fallback_only=args.fallback_only)

        tasks.append(("gmp", gmp))
    if selected or args.stocks:
        tasks.append(
            (
                "stocks",
                lambda: collect_market_data(
                    tuple(args.symbols), args.period, indicators=args.indicators
                ),
            )
        )
    if selected or args.news:

        def news():
            feeds = FEEDS
            if args.source:
                feeds = {k: v for k, v in FEEDS.items() if k.casefold() == args.source.casefold()}
                if not feeds:
                    raise ValueError("Unknown or disabled RSS publisher")
            return collect_news(
                feeds,
                max_items=args.limit,
                keywords=args.keywords,
                permission_reviewed=args.acknowledge_rss_terms,
            )

        tasks.append(("news", news))
    if selected or args.ipo:
        tasks.append(
            ("ipo", lambda: collect_ipo(args.ipo_file) if args.ipo_file else collect_ipo_market())
        )
    summary, failed = [], False
    for name, task in tasks:
        try:
            frame = task()
            errors = frame.attrs.get("errors", [])
            if name == "ipo" and not args.ipo_file:
                save(ipo_calendar(frame), "calendar", args.output / "ipo", args.snapshot)
                excluded = frame.attrs.get("excluded_records", [])
                save(
                    pd.DataFrame(
                        excluded,
                        columns=[
                            "ipo_name",
                            "provider_slug",
                            "reason",
                            "source_url",
                            "disclaimer",
                            "retrieved_at_utc",
                        ],
                    ),
                    "excluded_records",
                    args.output / "ipo",
                    args.snapshot,
                )
                conflicts = frame.attrs.get("conflicting_observations", [])
                save(
                    pd.DataFrame(conflicts, columns=frame.columns),
                    "ipo_conflicts",
                    args.output / "ipo",
                    args.snapshot,
                )
                update_registry(frame, args.output / "ipo" / "ipo_registry.sqlite")
                subscription_columns = [
                    "ipo_name",
                    "provider_slug",
                    "subscription_total",
                    "subscription_observed_at",
                    "source_updated_at",
                    "source_url",
                    "retrieved_at_utc",
                    "disclaimer",
                ]
                save(
                    frame[subscription_columns], "subscriptions", args.output / "ipo", args.snapshot
                )
            if name == "stocks":
                mask = frame.symbol.str.startswith("^")
                save(frame.loc[mask], "indices", args.output / "indices", args.snapshot)
                save(frame.loc[~mask], "stocks", args.output / "stocks", args.snapshot)
                # Preserve original combined output for existing consumers.
                save(frame, "market_data", args.output, args.snapshot)
            else:
                save(frame, name, args.output / name, args.snapshot)
                save(frame, name, args.output, args.snapshot)  # legacy paths
            status = (
                "partial"
                if errors and len(frame)
                else ("failed" if errors else ("ok" if len(frame) else "empty_or_disabled"))
            )
            summary.append(
                dict(collector=name, status=status, rows=len(frame), errors="; ".join(errors))
            )
            failed |= bool(errors)
            LOG.info("collector=%s status=%s rows=%s", name, status, len(frame))
        except Exception as exc:
            LOG.exception("collector_failed collector=%s", name)
            summary.append(dict(collector=name, status="failed", rows=0, errors=str(exc)))
            failed = True
    save(pd.DataFrame(summary), "run_summary", args.output / "logs", args.snapshot)
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
