"""Prevent accidental requests-network calls in the offline suite."""

import pytest
import requests


@pytest.fixture(autouse=True)
def block_unmocked_requests(monkeypatch):
    def blocked(*args, **kwargs):
        raise AssertionError("Offline test attempted an unmocked HTTP request")

    monkeypatch.setattr(requests.sessions.Session, "request", blocked)
