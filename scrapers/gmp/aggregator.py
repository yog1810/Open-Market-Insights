"""Priority-ordered collection; retain conflicting observations instead of averaging."""

import logging

import pandas as pd

from scrapers.http import USER_AGENT, PoliteClient

from .base import COLUMNS, GMPSource, parse_gmp_html

LOG = logging.getLogger(__name__)


def collect_gmp(
    sources: tuple[GMPSource, ...] = (),
    delay: float = 3.0,
    user_agent: str | None = None,
    *,
    client=None,
    fallback_only: bool = False,
) -> pd.DataFrame:
    if delay < 1:
        raise ValueError("delay must be >= 1 second")
    owned = client is None
    client = client or PoliteClient(interval=delay, user_agent=user_agent or USER_AGENT)
    rows, errors = [], []
    try:
        for source in sources:
            if source.permission_reviewed is not True or not source.permission_reference:
                LOG.warning(
                    "source_disabled source=%s reason=permission_not_documented", source.name
                )
                continue
            try:
                parsed = parse_gmp_html(client.get(source.url).text, source, strict=True)
                rows.extend(parsed)
                if fallback_only and parsed:
                    break
            except Exception as exc:
                errors.append(f"{source.name}: {exc}")
                LOG.warning("gmp_source_failed source=%s error=%s", source.name, exc)
    finally:
        if owned:
            client.close()
    frame = pd.DataFrame(rows, columns=COLUMNS)
    if not frame.empty:
        frame = frame.drop_duplicates(
            subset=[
                "ipo_slug",
                "gmp_inr",
                "issue_price",
                "source",
                "source_url",
                "source_updated_at",
            ]
        )
        frame["discrepancy"] = frame.groupby("ipo_slug")["gmp_inr"].transform("nunique") > 1
    frame = frame.reset_index(drop=True)
    frame.attrs["errors"] = errors
    return frame
