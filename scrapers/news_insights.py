"""RSS metadata aggregator. Feed endpoints may change or become unavailable."""
from __future__ import annotations
import logging
import time
from datetime import datetime, timezone
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import feedparser
import pandas as pd
import requests

LOG = logging.getLogger(__name__)
# These are candidate endpoints; verify feed URLs and publisher terms before use.
FEEDS = {
    "Economic Times": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "Mint": "https://www.livemint.com/rss/markets",
    "Business Standard": "https://www.business-standard.com/rss/markets-106.rss",
    # Moneycontrol: add a current, publisher-approved RSS URL after verification.
}
COLUMNS = ["publisher", "title", "url", "published", "retrieved_at_utc"]
UA = "open-market-insights/0.1 (research; set-your-email)"


def collect_news(feeds: dict[str, str] = FEEDS, delay: float = 2.0,
                 max_items: int = 30) -> pd.DataFrame:
    if delay < 1:
        raise ValueError("delay must be >= 1 second")
    session = requests.Session()
    session.headers.update({"User-Agent": UA, "Accept": "application/rss+xml,application/xml,text/xml"})
    rows = []
    for publisher, url in feeds.items():
        try:
            parsed_url = urlparse(url)
            robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
            robot_resp = session.get(robots_url, timeout=15)
            robot_resp.raise_for_status()
            robot = RobotFileParser()
            robot.parse(robot_resp.text.splitlines())
            if not robot.can_fetch(UA, url):
                LOG.warning("RSS access disallowed for %s", publisher)
                continue
            resp = session.get(url, timeout=20)
            resp.raise_for_status()
            parsed = feedparser.parse(resp.content)
            if parsed.bozo and not parsed.entries:
                LOG.warning("Malformed RSS for %s", publisher)
                continue
            for item in parsed.entries[:max_items]:
                title = item.get("title", "").strip()
                link = item.get("link", "").strip()
                if title and link:
                    rows.append({"publisher": publisher, "title": title, "url": link,
                                 "published": item.get("published", ""),
                                 "retrieved_at_utc": datetime.now(timezone.utc).isoformat()})
        except requests.RequestException as exc:
            LOG.warning("RSS request failed for %s: %s", publisher, exc)
        finally:
            time.sleep(delay)
    return pd.DataFrame(rows, columns=COLUMNS).drop_duplicates(subset=["url"])
