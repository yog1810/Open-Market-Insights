from dataclasses import replace
from unittest.mock import Mock

import pytest

from main import load_gmp_config
from scrapers.gmp import GMPSource, LayoutChanged, collect_gmp, parse_gmp_html
from scrapers.gmp.validators import money, normalize_name

SRC = GMPSource(
    "fixture",
    "https://example.org/gmp",
    "table",
    "tr",
    permission_reviewed=True,
    permission_reference="Synthetic permission test",
)
HTML = "<table><tr><td>Fictional Textiles IPO</td><td>₹25</td><td>₹100</td></tr></table>"


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("₹1,23,456.75", 123456.75),
        ("−₹12", -12),
        ("Rs. 0", 0),
        ("INR 50", 50),
        ("₹1,2,3", None),
        ("N/A", None),
        ("10%", None),
        ("100–150", None),
        ("NaN", None),
        ("inf", None),
        ("₹-", None),
    ],
)
def test_currency(text, expected):
    assert money(text) == expected


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("ABC Ltd. IPO", "abc-limited"),
        ("ABC Limited", "abc-limited"),
        ("आनंद IPO", "आनंद"),
        ("A & B", "a-and-b"),
    ],
)
def test_names(name, expected):
    assert normalize_name(name) == expected


def test_derived_values():
    row = parse_gmp_html(HTML, replace(SRC, issue_price_cell=2))[0]
    assert row["estimated_listing_price"] == 125
    assert row["gmp_percentage"] == 25
    assert "Unofficial" in row["estimate_basis"]
    assert row["raw_gmp"] == "₹25"
    assert row["source_updated_at"] is None


def test_unknown_price_not_derived():
    row = parse_gmp_html(HTML, SRC)[0]
    assert row["estimated_listing_price"] is None
    assert row["gmp_percentage"] is None


def test_multiple_tables():
    assert len(parse_gmp_html(HTML + HTML.replace("Textiles", "Foods"), SRC)) == 2


def test_header_change():
    with pytest.raises(LayoutChanged):
        parse_gmp_html(HTML, replace(SRC, expected_headers=("company", "gmp")))


def test_strict_missing_layout():
    with pytest.raises(LayoutChanged):
        parse_gmp_html("<html>Access blocked</html>", SRC, strict=True)


def test_disabled_no_network():
    client = Mock()
    assert collect_gmp([replace(SRC, enabled=False)], client=client).empty
    client.get.assert_not_called()


def test_fallback_and_error_isolation():
    client = Mock()
    client.get.side_effect = [TimeoutError("test"), Mock(text=HTML)]
    frame = collect_gmp([SRC, replace(SRC, name="fallback")], client=client)
    assert len(frame) == 1
    assert frame.iloc[0].source == "fallback"
    assert frame.attrs["errors"]


def test_disagreement_preserved_duplicates_removed():
    client = Mock()
    client.get.side_effect = [Mock(text=HTML + HTML), Mock(text=HTML.replace("₹25", "₹30"))]
    frame = collect_gmp([SRC, replace(SRC, name="second")], client=client)
    assert len(frame) == 2
    assert frame.discrepancy.all()
    assert set(frame.gmp_inr) == {25, 30}


def test_priority_fallback_only():
    client = Mock()
    client.get.return_value = Mock(text=HTML)
    assert len(collect_gmp([SRC, SRC], client=client, fallback_only=True)) == 1
    assert client.get.call_count == 1


def test_configuration_needs_no_permission_attestation(tmp_path):
    path = tmp_path / "sources.json"
    path.write_text('{"sources":[{"name":"x","url":"https://example.org/gmp"}]}')
    assert load_gmp_config(path)[0].enabled is True


def test_invalid_column():
    with pytest.raises(ValueError):
        replace(SRC, gmp_cell=-1)
