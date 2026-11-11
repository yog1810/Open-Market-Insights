"""Synthetic transport responses only: never access publisher sites in unit tests."""

from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from unittest.mock import Mock

import pytest
import requests

from scrapers.http import AccessDenied, PoliteClient


def response(status=200, text="User-agent: *\nAllow: /", headers=None):
    result = requests.Response()
    result.status_code = status
    result._content = text.encode()
    result.headers.update(headers or {})
    result.url = "https://example.org/data"
    return result


def client(responses, **kwargs):
    session, sleep = Mock(), Mock()
    session.get.side_effect = responses
    return PoliteClient(session=session, sleep=sleep, clock=lambda: 0, **kwargs), session, sleep


@pytest.mark.parametrize("status", [403, 404, 401])
def test_terminal_http_errors_no_retry(status):
    obj, session, _ = client([response(), response(status)])
    with pytest.raises(requests.HTTPError):
        obj.get("https://example.org/data")
    assert session.get.call_count == 2


@pytest.mark.parametrize("status", [429, 500, 502, 503, 504])
def test_transient_retries_and_paces(status):
    obj, session, sleep = client([response(), response(status), response(text="ok")])
    assert obj.get("https://example.org/data").text == "ok"
    assert session.get.call_count == 3
    assert all(call.kwargs["allow_redirects"] is False for call in session.get.call_args_list)
    assert all(call.kwargs["timeout"] == 20 for call in session.get.call_args_list)
    assert sleep.call_count >= 3


def test_retry_after_seconds():
    obj, _, sleep = client(
        [response(), response(429, headers={"Retry-After": "17"}), response(text="ok")]
    )
    obj.get("https://example.org/data")
    assert any(call.args == (17.0,) for call in sleep.call_args_list)


def test_retry_after_date():
    date = format_datetime(datetime.now(timezone.utc) + timedelta(seconds=30))
    obj, _, sleep = client(
        [response(), response(503, headers={"Retry-After": date}), response(text="ok")]
    )
    obj.get("https://example.org/data")
    assert any(27 <= call.args[0] <= 30 for call in sleep.call_args_list)


def test_long_retry_after_stops():
    obj, session, _ = client([response(), response(429, headers={"Retry-After": "3600"})])
    with pytest.raises(AccessDenied):
        obj.get("https://example.org/data")
    assert session.get.call_count == 2


def test_timeouts_exhausted():
    obj, session, _ = client([requests.Timeout()] * 3)
    with pytest.raises(requests.Timeout):
        obj.get("https://example.org/data")
    assert session.get.call_count == 3


def test_timeout_recovers():
    obj, _, _ = client([requests.Timeout(), response(), response(text="ok")])
    assert obj.get("https://example.org/data").text == "ok"


@pytest.mark.parametrize("policy", ["<html>blocked</html>", "", "User-agent: *\nDisallow: /"])
def test_policy_fails_closed(policy):
    obj, session, _ = client([response(text=policy)])
    with pytest.raises(AccessDenied):
        obj.get("https://example.org/data")
    assert session.get.call_count == 1


def test_crawl_delay_and_cache():
    obj, session, sleep = client(
        [response(text="User-agent: *\nCrawl-delay: 12\nAllow: /"), response(), response()]
    )
    obj.get("https://example.org/data")
    obj.get("https://example.org/other")
    assert session.get.call_count == 3
    assert all(call.args == (12,) for call in sleep.call_args_list)


@pytest.mark.parametrize(
    "url", ["http://example.org/a", "file:///tmp/x", "https://user:secret@example.org/x"]
)
def test_invalid_url_rejected(url):
    obj, session, _ = client([])
    with pytest.raises(ValueError):
        obj.get(url)
    session.get.assert_not_called()


def test_redirect_not_followed():
    obj, session, _ = client(
        [response(), response(302, headers={"Location": "https://elsewhere.test"})]
    )
    with pytest.raises(AccessDenied):
        obj.get("https://example.org/data")
    assert session.get.call_count == 2


def test_request_rate_respected():
    obj, _, sleep = client(
        [response(text="User-agent: *\nRequest-rate: 1/20\nAllow: /"), response()]
    )
    obj.get("https://example.org/data")
    assert sleep.call_args.args == (20,)


@pytest.mark.parametrize("kwargs", [{"interval": 0}, {"attempts": 0}, {"timeout": 0}])
def test_invalid_settings(kwargs):
    with pytest.raises(ValueError):
        PoliteClient(**kwargs)


def test_custom_user_agent_has_matching_robots_policy():
    obj, session, _ = client(
        [response(text="User-agent: research-project\nDisallow: /\nUser-agent: *\nAllow: /")],
        user_agent="research-project/1.0",
    )
    with pytest.raises(AccessDenied):
        obj.get("https://example.org/data")
    assert session.headers.update.call_args.args == ({"User-Agent": "research-project/1.0"},)
