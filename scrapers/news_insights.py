"""Metadata only. RSS access is distinct from publication/redistribution rights."""

from __future__ import annotations

import calendar
import logging
import re
from datetime import datetime, timezone
from urllib.parse import urlsplit

import feedparser
import pandas as pd

from scrapers.http import PoliteClient

LOG = logging.getLogger(__name__)
# Personal newsreader use only. CLI requires explicit acknowledgement.
CANDIDATE_FEEDS = {
    "Economic Times": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "Mint": "https://www.livemint.com/rss/marketsRSS",
}
FEEDS = {"Economic Times": CANDIDATE_FEEDS["Economic Times"]}
# Mint is advertised by its directory but returned HTTP 404 in the live check.
COLUMNS = [
    "publisher",
    "title",
    "url",
    "published",
    "category",
    "tags",
    "ipo_related",
    "retrieved_at_utc",
]


def parse_news(content: bytes, publisher: str, max_items=30, keywords=()) -> list[dict]:
    if max_items < 0:
        raise ValueError("max_items must be >= 0")
    parsed = feedparser.parse(content)
    if parsed.bozo and not parsed.entries:
        raise ValueError("Malformed or non-feed response")
    rows, seen = [], set()
    for item in parsed.entries:
        title, url = item.get("title", "").strip(), item.get("link", "").strip()
        parts = urlsplit(url)
        if not title or parts.scheme not in ("https", "http") or not parts.netloc or url in seen:
            continue
        tags = [word for word in keywords if word.casefold() in title.casefold()]
        if keywords and not tags:
            continue
        if len(rows) >= max_items:
            break
        seen.add(url)
        ipo = bool(re.search(r"\bIPO\b|initial public offer", title, re.I))
        stamp = item.get("published_parsed") or item.get("updated_parsed")
        published = (
            datetime.fromtimestamp(calendar.timegm(stamp), timezone.utc).isoformat()
            if stamp
            else None
        )
        rows.append(
            dict(
                publisher=publisher,
                title=title,
                url=url,
                published=published,
                category="ipo" if ipo else "markets",
                tags="|".join(tags),
                ipo_related=ipo,
                retrieved_at_utc=datetime.now(timezone.utc).isoformat(),
            )
        )
    return rows


def collect_news(
    feeds=None, delay=3.0, max_items=30, *, keywords=(), client=None, permission_reviewed=False
) -> pd.DataFrame:
    if delay < 1 or max_items < 0:
        raise ValueError("delay >= 1 and max_items >= 0 required")
    rows, errors = [], []
    if permission_reviewed is not True:
        LOG.warning("rss_disabled reason=personal_use_terms_not_acknowledged")
        return pd.DataFrame(columns=COLUMNS)
    owned = client is None
    client = client or PoliteClient(interval=delay)
    try:
        for publisher, url in (FEEDS if feeds is None else feeds).items():
            try:
                rows.extend(parse_news(client.get(url).content, publisher, max_items, keywords))
            except Exception as exc:
                errors.append(f"{publisher}: {exc}")
                LOG.warning("rss_source_failed source=%s error=%s", publisher, exc)
    finally:
        if owned:
            client.close()
    frame = (
        pd.DataFrame(rows, columns=COLUMNS).drop_duplicates(subset=["url"]).reset_index(drop=True)
    )
    frame.attrs["errors"] = errors
    return frame
