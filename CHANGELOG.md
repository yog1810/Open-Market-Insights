# Changelog

## 0.3.0 — 2026-11-12

- Added documented Xflot public IPO API collection as the default `--ipo` path.
- Added IPO registry, calendar, subscription totals and SQLite observation history.
- Retained ambiguous provider variants with explicit conflict flags and separate exports.
- Preserved API attribution/disclaimer and left unknown quote timestamps missing.
- Retained normalized local CSV/JSON import via `--ipo-file`.

## 0.2.1 — 2026-11-12

- Removed the blanket GMP written-permission attestation gate at the user's request;
  source availability now uses an explicit `enabled` flag.
- Added a live-tested IPOReports public-table adapter for personal research.
- Preserved full raw GMP cells, source update/status, subscription text and price
  bands; never infer a final issue price from a band or convert missing GMP to zero.
- Kept robots, pacing, retry/access controls and explicit restricted-source disablement.
- Added synthetic adapter tests and made CLI unit tests independent of live defaults.

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
