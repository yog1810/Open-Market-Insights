"""Conservative GMP adapters: selectors are examples, not guaranteed live mappings.

No bypass of access controls. robots.txt and site terms must permit automated access.
"""
from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import pandas as pd
import requests
from bs4 import BeautifulSoup

LOG = logging.getLogger(__name__)
USER_AGENT = "open-market-insights/0.1 (+https://github.com/yog1810/Open-Market-Insights; educational research)"


@dataclass(frozen=True)
class GMPSource:
    name: str
    url: str
    # TODO: Inspect permitted HTML manually; replace selectors after verification.
    table_selector: str = "table"
    row_selector: str = "tbody tr"
    name_cell: int = 0
    gmp_cell: int = 1


SOURCES = (
    GMPSource("Chittorgarh", "https://www.chittorgarh.com/"),
    GMPSource("IPOWatch", "https://ipowatch.in/"),
)


def _robots_allowed(session: requests.Session, url: str, agent: str) -> bool:
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    try:
        response = session.get(robots_url, timeout=15)
        response.raise_for_status()
        parser = RobotFileParser()
        parser.parse(response.text.splitlines())
        return parser.can_fetch(agent, url)
    except requests.RequestException as exc:
        LOG.warning("Could not verify robots.txt for %s: %s; skipping", url, exc)
        return False  # fail closed


def _money(text: str) -> float | None:
    """Return numeric GMP only for unambiguous currency-like strings."""
    clean = text.strip().replace(",", "")
    clean = re.sub(r"^(Rs\\.?\\s*|INR\\s*|₹\\s*)", "", clean, flags=re.I)
    clean = re.sub(r"^([+-])\\s*(Rs\\.?\\s*|INR\\s*|₹\\s*)", r"\\1", clean, flags=re.I)
    if re.fullmatch(r"[+-]?\d+(?:\.\d+)?", clean):
        return float(clean)
    return None


def parse_gmp_html(html: str, source: GMPSource) -> list[dict]:
    """Parse a *verified* table layout; skip ambiguous or incomplete rows."""
    soup = BeautifulSoup(html, "lxml")
    table = soup.select_one(source.table_selector)
    if table is None:
        LOG.warning("%s: table selector did not match", source.name)
        return []
    records = []
    for row in table.select(source.row_selector):
        cells = row.select("td")
        if len(cells) <= max(source.name_cell, source.gmp_cell):
            continue
        name = cells[source.name_cell].get_text(" ", strip=True)
        raw_gmp = cells[source.gmp_cell].get_text(" ", strip=True)
        gmp = _money(raw_gmp)
        if not name or gmp is None:
            continue
        records.append({"ipo_name": name, "gmp_inr": gmp, "raw_gmp": raw_gmp,
                        "source": source.name, "source_url": source.url,
                        "retrieved_at_utc": datetime.now(timezone.utc).isoformat()})
    return records


def collect_gmp(sources: tuple[GMPSource, ...] = SOURCES, delay: float = 3.0,
                user_agent: str = USER_AGENT) -> pd.DataFrame:
    """Disabled until source URLs and selectors are independently verified.

    This intentionally does not scrape homepages as if they were GMP tables.
    To enable a source: set its actual permitted GMP URL, verify selectors,
    confirm site terms, and call with verified source configuration.
    """
    if delay < 1:
        raise ValueError("delay must be >= 1 second")
    columns = ["ipo_name", "gmp_inr", "raw_gmp", "source", "source_url", "retrieved_at_utc"]
    session = requests.Session()
    session.headers.update({"User-Agent": user_agent, "Accept": "text/html,application/xhtml+xml"})
    records = []
    for source in sources:
        if source.url.rstrip("/") in {"https://www.chittorgarh.com", "https://ipowatch.in"}:
            LOG.warning("%s: example homepage only; configure verified GMP page URL", source.name)
            continue
        if not _robots_allowed(session, source.url, user_agent):
            LOG.warning("%s: disallowed or unverified robots policy; skipping", source.name)
            continue
        try:
            response = session.get(source.url, timeout=20)
            response.raise_for_status()
            records.extend(parse_gmp_html(response.text, source))
        except requests.RequestException as exc:
            LOG.warning("%s request failed: %s", source.name, exc)
        finally:
            time.sleep(delay)
    return pd.DataFrame(records, columns=columns)
