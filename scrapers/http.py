"""Fail-closed robots policy and paced, bounded HTTP transport; no bypasses."""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser

import requests

LOG = logging.getLogger(__name__)
USER_AGENT = "open-market-insights/0.2 (+https://github.com/yog1810/Open-Market-Insights; educational research)"


class AccessDenied(RuntimeError):
    """Policy, redirect or access control prevents collection."""


class PoliteClient:
    def __init__(
        self,
        session=None,
        interval=3.0,
        attempts=3,
        timeout=20,
        sleep=time.sleep,
        clock=time.monotonic,
        user_agent: str = USER_AGENT,
    ):
        if interval < 1 or not 1 <= attempts <= 5 or timeout <= 0:
            raise ValueError("interval >= 1, attempts 1..5 and positive timeout required")
        if not user_agent.strip():
            raise ValueError("A descriptive User-Agent is required")
        self.user_agent = user_agent
        self.session = session or requests.Session()
        self.session.headers.update({"User-Agent": self.user_agent})
        self.interval, self.attempts, self.timeout = interval, attempts, timeout
        self.sleep, self.clock = sleep, clock
        self.last: dict[str, float] = {}
        self.policies: dict[str, RobotFileParser] = {}

    def close(self) -> None:
        self.session.close()

    def _request(self, url: str, interval: float) -> requests.Response:
        host = urlsplit(url).netloc
        for attempt in range(self.attempts):
            if host in self.last:
                self.sleep(max(0, interval - (self.clock() - self.last[host])))
            self.last[host] = self.clock()
            try:
                response = self.session.get(url, timeout=self.timeout, allow_redirects=False)
            except (requests.Timeout, requests.ConnectionError):
                if attempt + 1 == self.attempts:
                    raise
                self.sleep(2**attempt)
                continue
            if 300 <= response.status_code < 400:
                raise AccessDenied(f"Redirect requires independent policy review: {url}")
            if response.status_code in (429, 500, 502, 503, 504) and attempt + 1 < self.attempts:
                wait = float(2**attempt)
                retry = response.headers.get("Retry-After")
                if retry:
                    try:
                        wait = max(wait, float(retry))
                    except ValueError:
                        try:
                            wait = max(
                                wait,
                                (
                                    parsedate_to_datetime(retry) - datetime.now(timezone.utc)
                                ).total_seconds(),
                            )
                        except (ValueError, TypeError, OverflowError):
                            pass
                if wait > 60:
                    raise AccessDenied(
                        f"Retry-After exceeds run budget; stop instead of retrying early: {url}"
                    )
                LOG.warning(
                    "http_retry url=%s status=%s attempt=%s wait=%s",
                    url,
                    response.status_code,
                    attempt + 1,
                    wait,
                )
                self.sleep(wait)
                continue
            response.raise_for_status()
            return response
        raise RuntimeError("Unreachable retry state")

    def get(self, url: str) -> requests.Response:
        parsed = urlsplit(url)
        if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
            raise ValueError("Only credential-free HTTPS URLs are supported")
        origin = f"{parsed.scheme}://{parsed.netloc}"
        if origin not in self.policies:
            response = self._request(origin + "/robots.txt", self.interval)
            content = response.text.lstrip("\ufeff")
            if not any(
                line.lower().strip().startswith("user-agent:") for line in content.splitlines()
            ):
                raise AccessDenied("Missing or malformed robots.txt; policy unverified")
            robot = RobotFileParser()
            robot.parse(content.splitlines())
            self.policies[origin] = robot
        robot = self.policies[origin]
        if not robot.can_fetch(self.user_agent, url):
            raise AccessDenied(f"robots.txt disallows {url}")
        interval = max(self.interval, robot.crawl_delay(self.user_agent) or 0)
        rate = robot.request_rate(self.user_agent)
        if rate:
            interval = max(interval, rate.seconds / rate.requests)
        return self._request(url, interval)
