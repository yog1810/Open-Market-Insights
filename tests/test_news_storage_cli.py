import json
import subprocess
import sys
from unittest.mock import Mock, patch

import pandas as pd
import pytest

from main import main
from scrapers.ipo_metadata import collect_ipo
from scrapers.news_insights import collect_news, parse_news
from scrapers.storage import save

RSS = b"""<rss version="2.0"><channel><title>Fixture</title>
<item><title>Fictional IPO opens</title><link>https://example.org/ipo</link><pubDate>Wed, 11 Nov 2026 10:00:00 +0530</pubDate><description>Never exported</description></item>
<item><title>Fictional IPO duplicate</title><link>https://example.org/ipo</link></item>
<item><title>Market news</title><link>https://example.org/market</link></item>
<item><title>Bad link</title><link>javascript:bad</link></item>
</channel></rss>"""


def test_news_dedup_dates_tags():
    rows = parse_news(RSS, "Fixture", keywords=("IPO",))
    assert len(rows) == 1
    assert rows[0]["published"] == "2026-11-11T04:30:00+00:00"
    assert rows[0]["category"] == "ipo"
    assert rows[0]["ipo_related"]
    assert "description" not in rows[0]


@pytest.mark.parametrize("limit", [0, 1, 2])
def test_news_limits(limit):
    assert len(parse_news(RSS, "Fixture", max_items=limit)) == limit


def test_news_malformed():
    with pytest.raises(ValueError):
        parse_news(b"<html>blocked", "Fixture")


def test_rss_disabled_at_api_level():
    client = Mock()
    assert collect_news(client=client).empty
    client.get.assert_not_called()


def test_news_source_isolation():
    client = Mock()
    client.get.side_effect = [TimeoutError(), Mock(content=RSS)]
    frame = collect_news(
        {"a": "https://a.test/feed", "b": "https://b.test/feed"},
        client=client,
        permission_reviewed=True,
    )
    assert len(frame) == 2
    assert len(frame.attrs["errors"]) == 1


@pytest.mark.parametrize("empty", [True, False])
def test_exports_unicode_null_and_empty(tmp_path, empty):
    frame = (
        pd.DataFrame(columns=["name", "value"])
        if empty
        else pd.DataFrame([{"name": "आनंद ₹", "value": None}] * 2)
    )
    save(frame, "records", tmp_path)
    rows = json.loads((tmp_path / "records.json").read_text())
    assert len(rows) == (0 if empty else 1)
    assert (tmp_path / "records.csv").read_text().startswith("name,value")
    if not empty:
        assert rows[0]["name"] == "आनंद ₹"
        assert rows[0]["value"] is None
    assert not list(tmp_path.glob("*.tmp"))


def test_snapshot(tmp_path):
    save(pd.DataFrame(columns=["a"]), "x", tmp_path, snapshot=True)
    assert len(list(tmp_path.glob("x_*.json"))) == 1


def test_atomic_failure_keeps_previous_file(tmp_path):
    (tmp_path / "x.csv").write_text("original")
    with patch("scrapers.storage.os.replace", side_effect=OSError("synthetic failure")):
        with pytest.raises(OSError):
            save(pd.DataFrame({"a": [1]}), "x", tmp_path)
    assert (tmp_path / "x.csv").read_text() == "original"
    assert not list(tmp_path.glob("*.tmp"))


@pytest.mark.parametrize("flag", ["--gmp", "--ipo", "--news"])
def test_cli_offline_subprocess(flag, tmp_path):
    result = subprocess.run(
        [sys.executable, "main.py", flag, "--output", str(tmp_path)], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr
    assert (tmp_path / "logs/run_summary.json").exists()


def test_all_collectors_isolated(tmp_path):
    with patch("main.collect_market_data", side_effect=RuntimeError("synthetic failure")):
        assert main(["--all", "--output", str(tmp_path)]) == 1
    summary = json.loads((tmp_path / "logs/run_summary.json").read_text())
    assert len(summary) == 4
    assert next(x for x in summary if x["collector"] == "stocks")["status"] == "failed"
    assert (tmp_path / "ipo/ipo.json").exists()


def test_unknown_source_fails(tmp_path):
    assert main(["--gmp", "--source", "typo", "--output", str(tmp_path)]) == 1


def test_ipo_import(tmp_path):
    path = tmp_path / "ipo.csv"
    path.write_text(
        "ipo_name,exchange,source_url,open_date,close_date,lot_size\nFictional Ltd,NSE,https://example.org/ipo,2026-11-01,2026-11-03,10\n"
    )
    frame = collect_ipo(path)
    assert frame.iloc[0].ipo_slug == "fictional-limited"
    assert frame.iloc[0].lot_size == 10


@pytest.mark.parametrize(
    "extra",
    [
        ",open_date,close_date\nFictional,NSE,https://example.org,2026-11-03,2026-11-01",
        ",lot_size\nFictional,NSE,https://example.org,-1",
        ",lot_size\nFictional,NSE,https://example.org,1.5",
    ],
)
def test_ipo_invalid_metadata(tmp_path, extra):
    path = tmp_path / "ipo.csv"
    path.write_text("ipo_name,exchange,source_url" + extra)
    with pytest.raises(ValueError):
        collect_ipo(path)


def test_ipo_infinite_price_rejected(tmp_path):
    path = tmp_path / "ipo.csv"
    path.write_text(
        "ipo_name,exchange,source_url,price_band_low\nFictional,NSE,https://example.org,inf\n"
    )
    with pytest.raises(ValueError):
        collect_ipo(path)
