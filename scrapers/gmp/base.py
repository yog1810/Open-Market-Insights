"""Explicit table layouts with independently configurable source availability."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from bs4 import BeautifulSoup

from .validators import money, normalize_name

LOG = logging.getLogger(__name__)
COLUMNS = [
    "ipo_name",
    "ipo_slug",
    "gmp_inr",
    "raw_gmp",
    "issue_price",
    "estimated_listing_price",
    "estimate_basis",
    "gmp_percentage",
    "source",
    "source_url",
    "source_updated_at",
    "retrieved_at_utc",
    "status",
    "discrepancy",
    "raw_issue_price",
    "subscription_status",
]


class LayoutChanged(ValueError):
    """Expected source layout is absent or contains no recognizable records."""


@dataclass(frozen=True)
class GMPSource:
    name: str
    url: str
    table_selector: str = "table"
    row_selector: str = "tbody tr"
    name_cell: int = 0
    gmp_cell: int = 1
    issue_price_cell: int | None = None
    updated_cell: int | None = None
    status_cell: int | None = None
    permission_reviewed: bool = False
    permission_reference: str = ""
    expected_headers: tuple[str, ...] = ()
    enabled: bool = True
    disabled_reason: str = ""

    def parse(self, html: str, strict: bool = False) -> list[dict]:
        return parse_gmp_html(html, self, strict=strict)

    def __post_init__(self):
        indices = (
            self.name_cell,
            self.gmp_cell,
            self.issue_price_cell,
            self.updated_cell,
            self.status_cell,
        )
        if any(i is not None and (not isinstance(i, int) or i < 0) for i in indices):
            raise ValueError("Column indices must be nonnegative integers")


def parse_gmp_html(html: str, source: GMPSource, strict=False) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    tables = soup.select(source.table_selector)
    records = []
    for table in tables:
        headers = [c.get_text(" ", strip=True).casefold() for c in table.select("th")]
        if source.expected_headers and tuple(headers) != source.expected_headers:
            raise LayoutChanged(f"{source.name}: table headers changed")
        for row in table.select(source.row_selector):
            cells = [c.get_text(" ", strip=True) for c in row.select("td")]
            if len(cells) <= max(source.name_cell, source.gmp_cell):
                continue
            name, raw = cells[source.name_cell], cells[source.gmp_cell]
            gmp = money(raw)
            if not name or not normalize_name(name) or gmp is None:
                LOG.warning("gmp_invalid_row source=%s name=%s raw_gmp=%s", source.name, name, raw)
                continue

            def cell(index):
                return cells[index] if index is not None and index < len(cells) else None

            price = money(cell(source.issue_price_cell) or "")
            if price is not None and price <= 0:
                price = None
            records.append(
                dict(
                    ipo_name=name,
                    ipo_slug=normalize_name(name),
                    gmp_inr=gmp,
                    raw_gmp=raw,
                    issue_price=price,
                    estimated_listing_price=price + gmp if price is not None else None,
                    estimate_basis="Unofficial issue price + GMP; not a prediction"
                    if price is not None
                    else None,
                    gmp_percentage=100 * gmp / price if price is not None else None,
                    source=source.name,
                    source_url=source.url,
                    # Unqualified dates are preserved verbatim, never assigned an invented timezone.
                    source_updated_at=cell(source.updated_cell),
                    retrieved_at_utc=datetime.now(timezone.utc).isoformat(),
                    status=cell(source.status_cell) or "observed",
                    discrepancy=False,
                )
            )
    if strict and not records:
        raise LayoutChanged(
            f"{source.name}: no valid GMP rows; layout changed, empty page or invalid values"
        )
    return records
