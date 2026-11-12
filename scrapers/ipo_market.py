"""Documented public Xflot API: attribution, original disclaimer, >=60s pacing.

A public API is provider-reported information, not official exchange verification.
The bulk endpoint has no individual GMP/subscription observation timestamps.
"""

from __future__ import annotations

import logging
import math
import re
from datetime import datetime, timezone

import pandas as pd

from scrapers.gmp.validators import normalize_name
from scrapers.http import PoliteClient

LOG = logging.getLogger(__name__)
URL = "https://www.xflot.com/api/public/market/ipos?limit=200"
SOURCE_URL = "https://www.xflot.com/api-docs"
COLUMNS = [
    "ipo_name",
    "ipo_slug",
    "provider_slug",
    "board",
    "status",
    "sector",
    "exchange",
    "symbol",
    "registrar",
    "open_date",
    "close_date",
    "allotment_date",
    "listing_date",
    "price_band_low",
    "price_band_high",
    "lot_size",
    "issue_size_cr",
    "issue_price",
    "listing_price",
    "gmp_inr",
    "gmp_source_count",
    "gmp_spread",
    "gmp_disputed",
    "subscription_total",
    "source_updated_at",
    "gmp_observed_at",
    "subscription_observed_at",
    "lifecycle_conflicted",
    "source",
    "source_url",
    "provider_record_url",
    "retrieved_at_utc",
    "disclaimer",
    "record_conflicted",
    "variant_count",
]


def _number(value, *, minimum=None, integer=False):
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError("Invalid numeric field")
    if minimum is not None and value < minimum or integer and int(value) != value:
        raise ValueError("Invalid numeric range")
    return int(value) if integer else float(value)


def _date(value):
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("Invalid timestamp type")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Timestamp requires explicit timezone")
    return parsed.astimezone(timezone.utc).isoformat()


def parse_ipo_market(payload: dict, now: datetime | None = None) -> pd.DataFrame:
    now = now or datetime.now(timezone.utc)
    if payload.get("ok") is not True or not isinstance(payload.get("ipos"), list):
        raise ValueError("Unexpected IPO API envelope")
    disclaimer = payload.get("disclaimer")
    if not isinstance(disclaimer, str) or not disclaimer.strip():
        raise ValueError("Provider disclaimer missing; cannot publish this feed")
    rows, errors, excluded = [], [], []
    for item in payload["ipos"]:
        try:
            name, slug = item["name"], item["slug"]

            if (
                not isinstance(name, str)
                or not name.strip()
                or not isinstance(slug, str)
                or not re.fullmatch("[a-z0-9]+(?:-[a-z0-9]+)*", slug)
            ):
                raise ValueError("Invalid company identity")
            if item["board"] not in ("MAINBOARD", "SME") or item["status"] not in (
                "UPCOMING",
                "OPEN",
                "CLOSED",
                "LISTED",
            ):
                raise ValueError("Unknown board/status")
            if re.search(
                r"\b(?:NCD|ZCZP|FPO|FPSE|Issue\s+Withdrawn|Issue\s+postponed|Withdrawal\s+Window|Special\s+Withdrawal\s+Option|Social\s+Enterprise)\b",
                name,
                re.I,
            ):
                excluded.append(
                    dict(
                        ipo_name=name,
                        provider_slug=slug,
                        reason="Non-IPO instrument or withdrawn/postponed issue",
                        source_url=SOURCE_URL,
                        disclaimer=disclaimer,
                        retrieved_at_utc=now.isoformat(),
                    )
                )
                continue
            low = _number(item.get("priceMin"), minimum=0.01)
            high = _number(item.get("priceMax"), minimum=0.01)
            if low is not None and high is not None and low > high:
                raise ValueError("Inverted price band")
            opened, closed = _date(item.get("openDate")), _date(item.get("closeDate"))
            if opened and closed and opened > closed:
                raise ValueError("Inverted bidding dates")
            updated = _date(item.get("updatedAt"))
            if updated and datetime.fromisoformat(updated).timestamp() > now.timestamp() + 300:
                raise ValueError("Future provider update")
            sources = _number(item.get("gmpSources"), minimum=0, integer=True)
            gmp = _number(item.get("lastGmp"))
            if gmp == 0 and sources == 0:
                gmp = None  # unsupported zero cannot establish an observed premium
            lifecycle = item.get("lifecycle") or {}
            listed = _date(item.get("listingDate"))
            conflict = bool(lifecycle.get("conflicted")) or bool(
                listed and closed and listed <= closed
            )
            rows.append(
                dict(
                    ipo_name=name.strip(),
                    ipo_slug=normalize_name(name),
                    provider_slug=slug,
                    board=item["board"],
                    status=item["status"],
                    sector=item.get("sector"),
                    exchange=item.get("exchange"),
                    symbol=item.get("symbol"),
                    registrar=item.get("registrar"),
                    open_date=opened,
                    close_date=closed,
                    allotment_date=_date(item.get("allotmentDate")),
                    listing_date=listed,
                    price_band_low=low,
                    price_band_high=high,
                    lot_size=_number(item.get("lotSize"), minimum=1, integer=True),
                    issue_size_cr=_number(item.get("issueSizeCr"), minimum=0),
                    issue_price=_number(item.get("issuePrice"), minimum=0.01),
                    listing_price=_number(item.get("listingPrice"), minimum=0.01),
                    gmp_inr=gmp,
                    gmp_source_count=sources,
                    gmp_spread=_number(item.get("gmpSpread"), minimum=0),
                    gmp_disputed=bool(item.get("gmpDisputed")),
                    subscription_total=_number(item.get("lastSubX"), minimum=0),
                    source_updated_at=updated,
                    gmp_observed_at=None,
                    subscription_observed_at=None,
                    lifecycle_conflicted=conflict,
                    source="Xflot public API",
                    source_url=SOURCE_URL,
                    provider_record_url="https://www.xflot.com/ipo/" + slug,
                    retrieved_at_utc=now.isoformat(),
                    disclaimer=disclaimer,
                )
            )
        except (ValueError, TypeError, KeyError, AttributeError) as exc:
            errors.append(
                f"{item.get('slug', 'unknown') if isinstance(item, dict) else 'invalid row'}: {exc}"
            )
    frame = pd.DataFrame(rows, columns=COLUMNS)
    # Rows may contain a list of exchanges. Preserve it as compact JSON rather
    # than stringify with Python repr or inventing an exchange designation.
    import json

    for col in ("exchange", "registrar"):
        frame[col] = frame[col].map(
            lambda x: json.dumps(x, ensure_ascii=False) if isinstance(x, (dict, list)) else x
        )
    frame = frame.drop_duplicates().reset_index(drop=True)
    variants = []
    preferred = []
    for slug, group in frame.groupby("provider_slug", sort=False):
        candidates = group.to_dict("records")
        conflict = len(candidates) > 1
        for row in candidates:
            row["record_conflicted"] = conflict
            row["variant_count"] = len(candidates)

        def rank(row):
            fields = [
                "price_band_low",
                "price_band_high",
                "lot_size",
                "open_date",
                "close_date",
                "listing_date",
                "gmp_inr",
                "subscription_total",
            ]
            return (sum(pd.notna(row[field]) for field in fields), row["source_updated_at"] or "")

        preferred.append(max(candidates, key=rank))
        if conflict:
            variants.extend(candidates)
    frame = pd.DataFrame(preferred, columns=COLUMNS)
    frame.attrs["excluded_records"] = excluded
    frame.attrs["conflicting_observations"] = variants
    frame.attrs["errors"] = errors
    return frame


def collect_ipo_market(*, client=None) -> pd.DataFrame:
    owned = client is None
    client = client or PoliteClient(interval=60, attempts=1)
    try:
        return parse_ipo_market(client.get(URL).json())
    finally:
        if owned:
            client.close()


def ipo_calendar(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for item in frame.to_dict("records"):
        for field, kind in [
            ("open_date", "BIDDING_OPENS"),
            ("close_date", "BIDDING_CLOSES"),
            ("allotment_date", "ALLOTMENT_EXPECTED"),
            ("listing_date", "LISTING_REPORTED"),
        ]:
            if pd.notna(item[field]):
                rows.append(
                    dict(
                        ipo_name=item["ipo_name"],
                        provider_slug=item["provider_slug"],
                        event=kind,
                        date_utc=item[field],
                        source_url=item["source_url"],
                        source_updated_at=item["source_updated_at"],
                        retrieved_at_utc=item["retrieved_at_utc"],
                        lifecycle_conflicted=item["lifecycle_conflicted"]
                        or item["record_conflicted"],
                        disclaimer=item["disclaimer"],
                    )
                )
    columns = [
        "ipo_name",
        "provider_slug",
        "event",
        "date_utc",
        "source_url",
        "source_updated_at",
        "retrieved_at_utc",
        "lifecycle_conflicted",
        "disclaimer",
    ]
    return pd.DataFrame(rows, columns=columns).sort_values("date_utc").reset_index(drop=True)
