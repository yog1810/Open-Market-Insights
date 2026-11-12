import json
import sqlite3
from datetime import datetime, timezone
from unittest.mock import Mock

import pandas as pd
import pytest

from scrapers.ipo_market import collect_ipo_market, ipo_calendar, parse_ipo_market
from scrapers.registry import update_registry

NOW = datetime(2026, 11, 12, tzinfo=timezone.utc)


def payload(**updates):
    row = dict(
        name="Fictional Engineering",
        slug="fictional-engineering",
        board="MAINBOARD",
        status="CLOSED",
        priceMin=100,
        priceMax=110,
        lotSize=100,
        openDate="2026-11-01T00:00:00Z",
        closeDate="2026-11-03T00:00:00Z",
        allotmentDate="2026-11-05T00:00:00Z",
        listingDate="2026-11-07T00:00:00Z",
        updatedAt="2026-11-11T12:00:00Z",
        gmpSources=1,
        lastGmp=0,
        lastSubX=3.5,
        issueSizeCr=25,
    )
    row.update(updates)
    return dict(ok=True, ipos=[row], disclaimer="Synthetic provider disclaimer")


def test_registry_metadata_and_units():
    row = parse_ipo_market(payload(), NOW).iloc[0]
    assert row.issue_size_cr == 25
    assert row.lot_size == 100
    assert row.issue_price is None
    assert row.gmp_inr == 0
    assert row.gmp_observed_at is None
    assert row.subscription_observed_at is None
    assert row.disclaimer == "Synthetic provider disclaimer"


@pytest.mark.parametrize(
    "bad",
    [
        dict(priceMin=200),
        dict(lotSize=0),
        dict(lotSize=True),
        dict(priceMax=float("inf")),
        dict(lastSubX=-1),
        dict(openDate="2026-11-08T00:00:00Z"),
        dict(updatedAt="2026-12-01T00:00:00Z"),
        dict(status="UNKNOWN"),
        dict(openDate="2026-11-01"),
        dict(slug="../unsafe"),
    ],
)
def test_bad_rows_isolated(bad):
    frame = parse_ipo_market(payload(**bad), NOW)
    assert frame.empty
    assert len(frame.attrs["errors"]) == 1


def test_requires_disclaimer():
    data = payload()
    data.pop("disclaimer")
    with pytest.raises(ValueError):
        parse_ipo_market(data, NOW)


def test_source_free_zero_missing():
    assert parse_ipo_market(payload(gmpSources=0), NOW).iloc[0].gmp_inr is None


def test_negative_gmp_and_duplicates():
    data = payload(lastGmp=-5)
    data["ipos"] *= 2
    result = parse_ipo_market(data, NOW)
    assert len(result) == 1
    assert result.iloc[0].gmp_inr == -5


def test_calendar_not_invented():
    frame = parse_ipo_market(payload(allotmentDate=None), NOW)
    calendar = ipo_calendar(frame)
    assert len(calendar) == 3
    assert "ALLOTMENT_EXPECTED" not in set(calendar.event)
    assert calendar.date_utc.is_monotonic_increasing


def test_empty_calendar_schema():
    assert list(
        ipo_calendar(parse_ipo_market(dict(ok=True, ipos=[], disclaimer="fixture"), NOW)).columns
    )


def test_api_mocked():
    client = Mock()
    client.get.return_value.json.return_value = payload()
    assert len(collect_ipo_market(client=client)) == 1
    assert client.get.call_count == 1


def test_sqlite_idempotent_and_history(tmp_path):
    path = tmp_path / "ipo.sqlite"
    frame = parse_ipo_market(payload(), NOW)
    assert update_registry(frame, path) == 1
    assert update_registry(frame, path) == 1
    newer = frame.copy()
    newer["retrieved_at_utc"] = "2026-11-13T00:00:00+00:00"
    assert update_registry(newer, path) == 2
    with sqlite3.connect(path) as db:
        raw = db.execute("select payload from ipo_observation limit 1").fetchone()[0]
    assert json.loads(raw)["issue_price"] is None


def test_empty_registry(tmp_path):
    assert (
        update_registry(
            pd.DataFrame(columns=["source", "provider_slug", "retrieved_at_utc"]),
            tmp_path / "empty.sqlite",
        )
        == 0
    )


def test_conflicting_provider_variants_preserved(tmp_path):
    data = payload(lastGmp=5)
    alternate = dict(data["ipos"][0], lastGmp=15)
    data["ipos"].append(alternate)
    frame = parse_ipo_market(data, NOW)
    assert len(frame) == 1
    assert frame.iloc[0].record_conflicted
    variants = frame.attrs["conflicting_observations"]
    assert {row["gmp_inr"] for row in variants} == {5, 15}
    assert update_registry(frame, tmp_path / "conflicts.sqlite") == 2


@pytest.mark.parametrize(
    "name",
    [
        "Fictional NCD",
        "Fictional FPO",
        "Fictional - Issue Withdrawn",
        "Fictional Social Enterprise",
    ],
)
def test_non_ipo_instruments_not_misrepresented(name):
    frame = parse_ipo_market(payload(name=name), NOW)
    assert frame.empty
    assert len(frame.attrs["excluded_records"]) == 1
    assert frame.attrs["errors"] == []
