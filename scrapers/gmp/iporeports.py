"""IPOReports public first-page GMP table; personal informational research.

Terms allow personal research and prohibit abusive scraping. Robots is checked at
runtime. Neither availability nor this adapter grants public redistribution rights.
"""

import logging
from datetime import datetime, timezone

from bs4 import BeautifulSoup

from .base import GMPSource, LayoutChanged
from .validators import money, normalize_name

LOG = logging.getLogger(__name__)
HEADERS = (
    "ipo name",
    "gmp (₹)",
    "rating",
    "sub",
    "issue price (₹)",
    "lot",
    "ipo size (₹)",
    "open",
    "close",
    "boarding date",
    "listing date",
    "allotment check",
    "last updated at",
)


class IPOReportsSource(GMPSource):
    def parse(self, html: str, strict: bool = False) -> list[dict]:
        soup = BeautifulSoup(html, "lxml")
        table = soup.select_one("#ipo-main-table")
        if table is None:
            raise LayoutChanged("iporeports: #ipo-main-table not found")
        headers = tuple(th.get_text(" ", strip=True).casefold() for th in table.select("thead th"))
        if headers != HEADERS:
            raise LayoutChanged("iporeports: table header signature changed")
        records = []
        for tr in table.select("tbody tr"):
            cells = tr.find_all("td", recursive=False)
            if len(cells) != len(HEADERS):
                raise LayoutChanged("iporeports: row width changed")
            anchor = cells[0].select_one("a.ipo-name-link")
            if anchor is None:
                raise LayoutChanged("iporeports: issuer anchor missing")
            name = anchor.get_text(" ", strip=True)
            # The inspected cell is "₹8 <br><strong>(9.76%)</strong>".
            # Parse only its direct numeric text, never the adjacent percentage.
            value_text = " ".join(
                t.strip() for t in cells[1].find_all(string=True, recursive=False) if t.strip()
            )
            value = money(value_text)
            if not name or not normalize_name(name) or value is None:
                LOG.warning(
                    "gmp_missing_or_invalid source=iporeports name=%s raw=%s",
                    name,
                    cells[1].get_text(" ", strip=True),
                )
                continue
            badge = cells[0].select_one("small.badge")
            records.append(
                dict(
                    ipo_name=name,
                    ipo_slug=normalize_name(name),
                    gmp_inr=value,
                    raw_gmp=cells[1].get_text(" ", strip=True),
                    # The displayed issue-price cell is a band, not a confirmed final price.
                    issue_price=None,
                    raw_issue_price=cells[4].get_text(" ", strip=True),
                    estimated_listing_price=None,
                    estimate_basis=None,
                    gmp_percentage=None,
                    source=self.name,
                    source_url=self.url,
                    source_updated_at=cells[12].get_text(" ", strip=True) or None,
                    retrieved_at_utc=datetime.now(timezone.utc).isoformat(),
                    status=badge.get_text(" ", strip=True) if badge else "observed",
                    subscription_status=cells[3].get_text(" ", strip=True) or None,
                    discrepancy=False,
                )
            )
        if strict and not records:
            raise LayoutChanged("iporeports: no valid GMP rows")
        return records


SOURCE = IPOReportsSource("iporeports", "https://iporeports.in/", table_selector="#ipo-main-table")
