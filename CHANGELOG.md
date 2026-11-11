# Changelog

## 0.2.0 — 2026-11-12

- Added a modular, permission-gated GMP adapter system with priority/fallback,
  strict INR parsing, conservative Unicode company keys, provenance, optional
  derived values and retained discrepancy observations.
- Added robots fail-closed HTTP transport, host pacing, crawl-delay/request-rate,
  bounded retries, Retry-After handling, timeouts and redirect refusal.
- Validated daily Yahoo OHLCV, normalized UTC times, added BSE defaults, indicators,
  retry/error isolation and explicit delayed/unadjusted attribution.
- Verified ET RSS; disabled Mint after advertised endpoint returned 404; restricted default feeds to personal-use opt-in;
  added deduplication, tagging, IPO detection and UTC metadata timestamps.
- Added validated local IPO metadata import instead of prohibited exchange scraping.
- Added atomic UTF-8 CSV/JSON exports, snapshots, category directories, legacy
  output paths and machine-readable run summaries with partial/failure exit status.
- Added offline parser/HTTP/market/RSS/storage/CLI tests and Python 3.10–3.13 CI.
- Documented source research, licensing, limitations and validation evidence.

## 0.1.0

- Initial GMP table parser, yfinance collector, RSS candidates and CLI scaffold.
