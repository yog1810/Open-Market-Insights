"""Disabled: written permission required; live selectors intentionally unverified."""

from .base import GMPSource

SOURCE = GMPSource(
    "investorgain",
    "https://www.investorgain.com/report/ipo-gmp-live/331/",
    enabled=False,
    disabled_reason="Published restrictions; no live mapping",
)
