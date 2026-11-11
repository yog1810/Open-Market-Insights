"""Backward-compatible imports for the original public API."""

from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser

import requests

from scrapers.gmp import GMPSource, collect_gmp, parse_gmp_html
from scrapers.gmp.validators import money as _money
from scrapers.http import USER_AGENT

SOURCES = ()


def _robots_allowed(session, url, agent):
    """Compatibility helper. Production collectors use the paced PoliteClient."""
    parsed = urlsplit(url)
    try:
        response = session.get(f"{parsed.scheme}://{parsed.netloc}/robots.txt", timeout=15)
        response.raise_for_status()
        robot = RobotFileParser()
        robot.parse(response.text.splitlines())
        return robot.can_fetch(agent, url)
    except requests.RequestException:
        return False


__all__ = ["GMPSource", "parse_gmp_html", "collect_gmp", "SOURCES", "USER_AGENT", "_money"]
