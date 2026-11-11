"""Synthetic markup representing the verified layout; no copied publisher dataset."""

from unittest.mock import Mock

import pytest

from scrapers.gmp import LayoutChanged, collect_gmp
from scrapers.gmp.iporeports import HEADERS, SOURCE


def markup(
    gmp="₹12", percentage="(6%)", price="₹180 – ₹200 per share", name="Fictional Widgets IPO"
):
    headers = "".join(f"<th>{x}</th>" for x in HEADERS)
    columns = [
        f'<a class="ipo-name-link">{name}</a><small class="badgeT">Mainboard</small><small class="badge badge-listed">Listed</small>',
        f"{gmp}<br><strong>{percentage}</strong>",
        "rating",
        "2.5x",
        price,
        "10",
        "size",
        "open",
        "close",
        "boarding",
        "listing",
        "allotment",
        "2026-11-01 12:30",
    ]
    return (
        '<table id="ipo-main-table"><thead><tr>'
        + headers
        + "</tr></thead><tbody><tr>"
        + "".join(f"<td>{c}</td>" for c in columns)
        + "</tr></tbody></table>"
    )


def test_amount_not_percentage_or_badges():
    row = SOURCE.parse(markup(), strict=True)[0]
    assert row["ipo_name"] == "Fictional Widgets IPO"
    assert row["gmp_inr"] == 12
    assert row["raw_gmp"] == "₹12 (6%)"
    assert row["status"] == "Listed"
    assert row["subscription_status"] == "2.5x"
    assert row["source_updated_at"] == "2026-11-01 12:30"
    assert row["raw_issue_price"] == "₹180 – ₹200 per share"
    assert row["issue_price"] is None
    assert row["estimated_listing_price"] is None


@pytest.mark.parametrize(("value", "expected"), [("₹0", 0), ("-₹8", -8), ("₹1,250", 1250)])
def test_currency(value, expected):
    assert SOURCE.parse(markup(value))[0]["gmp_inr"] == expected


@pytest.mark.parametrize("value", ["—", "NA", "₹-", "₹12–14", ""])
def test_no_fabricated_missing_value(value):
    assert SOURCE.parse(markup(value)) == []


def test_changed_header():
    with pytest.raises(LayoutChanged):
        SOURCE.parse(markup().replace("<th>gmp (₹)</th>", "<th>new</th>"))


def test_provider_dispatch_without_permission_attestation():
    client = Mock()
    client.get.return_value = Mock(text=markup())
    frame = collect_gmp([SOURCE], client=client)
    assert len(frame) == 1
    assert frame.iloc[0].gmp_inr == 12
    assert "raw_issue_price" in frame
