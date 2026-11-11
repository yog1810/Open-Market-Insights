"""CLI entrypoint: python main.py --all"""
from __future__ import annotations
import argparse
import json
import logging
from pathlib import Path
import pandas as pd
from scrapers.gmp_scraper import collect_gmp, GMPSource
from scrapers.market_data import collect_market_data, DEFAULT_SYMBOLS
from scrapers.news_insights import collect_news

LOG = logging.getLogger("open_market_insights")


def save(df: pd.DataFrame, name: str, output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    csv_path = output / f"{name}.csv"
    json_path = output / f"{name}.json"
    df.to_csv(csv_path, index=False)
    df.to_json(json_path, orient="records", indent=2, force_ascii=False)
    LOG.info("%s: %s rows saved to %s and %s", name, len(df), csv_path, json_path)


def _skip_news() -> pd.DataFrame:
    LOG.warning("RSS disabled by default; review publisher terms and pass --acknowledge-rss-terms for permitted personal use")
    return pd.DataFrame(columns=["publisher", "title", "url", "published", "retrieved_at_utc"])


def load_gmp_config(path: Path) -> tuple[GMPSource, ...]:
    """Load explicit, user-reviewed GMP page mappings; never guess selectors."""
    config = json.loads(path.read_text(encoding="utf-8"))
    sources = []
    for item in config["sources"]:
        if not item.get("permission_reviewed", False):
            LOG.warning("Skipping %s: permission_reviewed must be true", item.get("name"))
            continue
        if not item["url"].startswith("https://"):
            raise ValueError("GMP source URLs must use HTTPS")
        sources.append(GMPSource(
            name=item["name"], url=item["url"],
            table_selector=item["table_selector"],
            row_selector=item.get("row_selector", "tbody tr"),
            name_cell=int(item["name_cell"]), gmp_cell=int(item["gmp_cell"])
        ))
    return tuple(sources)


def main() -> None:
    parser = argparse.ArgumentParser(description="Free Indian market data collector")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--all", action="store_true", help="Collect all categories (default)")
    group.add_argument("--gmp", action="store_true", help="Collect configured GMP sources")
    group.add_argument("--stocks", action="store_true", help="Collect stock/index history")
    group.add_argument("--news", action="store_true", help="Collect RSS metadata")
    parser.add_argument("--symbols", nargs="+", default=list(DEFAULT_SYMBOLS))
    parser.add_argument("--period", default="5d", help="Yahoo Finance history period")
    parser.add_argument("--gmp-config", type=Path, help="JSON config with verified GMP source URLs and selectors")
    parser.add_argument("--output", type=Path, default=Path("data"))
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--acknowledge-rss-terms", action="store_true", help="Opt in to permitted personal, noncommercial RSS use")
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    all_selected = args.all or not (args.gmp or args.stocks or args.news)
    tasks = []
    if all_selected or args.gmp:
        tasks.append(("gmp", lambda: collect_gmp(load_gmp_config(args.gmp_config)) if args.gmp_config else collect_gmp()))
    if all_selected or args.stocks:
        tasks.append(("market_data", lambda: collect_market_data(tuple(args.symbols), args.period)))
    if all_selected or args.news:
        tasks.append(("news", lambda: collect_news() if args.acknowledge_rss_terms else _skip_news()))
    for name, task in tasks:
        try:
            save(task(), name, args.output)
        except Exception:
            LOG.exception("Unexpected error in %s; continuing", name)


if __name__ == "__main__":
    main()
