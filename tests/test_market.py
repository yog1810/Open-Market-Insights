from unittest.mock import Mock, patch

import pandas as pd
import pytest

from scrapers.market_data import collect_market_data, normalize_history


def history(n=1):
    return pd.DataFrame(
        {
            "Open": [100 + i for i in range(n)],
            "High": [102 + i for i in range(n)],
            "Low": [99 + i for i in range(n)],
            "Close": [101 + i for i in range(n)],
            "Volume": [123] * n,
        },
        index=pd.date_range("2026-01-01", periods=n),
    )


def test_normalize_timezone():
    frame = normalize_history(history(), "TCS.NS")
    assert frame.iloc[0].date == "2025-12-31T18:30:00+00:00"
    assert frame.iloc[0].volume == 123


def test_aware_timezone():
    data = history()
    data.index = data.index.tz_localize("Asia/Kolkata")
    assert normalize_history(data, "TCS.NS").iloc[0].date.endswith("+00:00")


@pytest.mark.parametrize(
    ("column", "value"),
    [
        ("Close", float("nan")),
        ("Close", float("inf")),
        ("High", 50),
        ("Low", 200),
        ("Open", -1),
        ("Volume", -2),
        ("Volume", 1.5),
    ],
)
def test_invalid_prices(column, value):
    data = history().astype(float)
    data.iloc[0, data.columns.get_loc(column)] = value
    assert normalize_history(data, "TCS.NS").empty


def test_missing_volume_retained():
    data = history().astype(float)
    data["Volume"] = float("nan")
    assert pd.isna(normalize_history(data, "TCS.NS").iloc[0].volume)


def test_missing_columns():
    with pytest.raises(ValueError):
        normalize_history(history().drop(columns="Open"), "TCS.NS")


@pytest.mark.parametrize("reverse", [False, True])
def test_multiindex(reverse):
    data = history()
    data.columns = pd.MultiIndex.from_tuples(
        [(c, "TCS.NS") if not reverse else ("TCS.NS", c) for c in data.columns]
    )
    assert len(normalize_history(data, "TCS.NS")) == 1


def test_indicators_and_warmup():
    data = normalize_history(history(60), "TCS.NS", True)
    assert data.sma_20.iloc[:19].isna().all()
    assert data.sma_20.iloc[19] == pytest.approx(110.5)
    assert data.sma_50.iloc[49] == pytest.approx(125.5)
    assert data.rsi_14.iloc[:14].isna().all()
    assert data.rsi_14.iloc[14] == 100
    assert data.daily_change_pct.iloc[1] == pytest.approx(100 / 101)


def test_stock_retry_and_symbol_isolation():
    ticker = Mock()
    ticker.history.side_effect = [
        TimeoutError(),
        history(),
        pd.DataFrame(),
        pd.DataFrame(),
        pd.DataFrame(),
    ]
    with patch("scrapers.market_data.yf.Ticker", return_value=ticker):
        result = collect_market_data(("TCS.NS", "INVALID.NS"), sleep=lambda _: None)
    assert len(result) == 1
    assert len(result.attrs["errors"]) == 1
    assert ticker.history.call_count == 5


def test_rate_limit_not_retried():
    with patch("scrapers.market_data.yf.Ticker") as ticker:
        ticker.return_value.history.side_effect = RuntimeError("HTTP 429")
        result = collect_market_data(("TCS.NS",), sleep=lambda _: None)
    assert result.empty
    assert ticker.return_value.history.call_count == 1


def test_invalid_period():
    with pytest.raises(ValueError):
        collect_market_data(period="bad")


def test_ticker_deduplication():
    with patch("scrapers.market_data.yf.Ticker") as ticker:
        ticker.return_value.history.return_value = history()
        assert len(collect_market_data(("TCS.NS", "TCS.NS"), sleep=lambda _: None)) == 1
        assert ticker.call_count == 1


def test_rejected_rows_report_partial_result():
    data = history(2).astype(float)
    data.iloc[0, data.columns.get_loc("Close")] = float("nan")
    with patch("scrapers.market_data.yf.Ticker") as ticker:
        ticker.return_value.history.return_value = data
        frame = collect_market_data(("TCS.NS",), sleep=lambda _: None)
    assert len(frame) == 1
    assert len(frame.attrs["errors"]) == 1
