# Validation — 12 November 2026 (IST)

## Executed local checks

Runtime: Python 3.12. Dependencies installed in an isolated virtual environment.
Notable installed versions: pandas 3.1.1, yfinance 1.8.0, requests 2.34.2,
BeautifulSoup 4.15.0, lxml 6.1.3, feedparser 6.0.14, pytest 9.2.0, ruff 0.17.4.

| Check | Actual result |
| --- | --- |
| `python -m pytest -q --tb=short` | 101 passed, 0 failed, 0 skipped; additionally 6 unittest subtests passed |
| `python -m unittest discover -s tests -v` | Original compatibility suite: 9 passed, 0 failed |
| `python -m ruff check .` | Passed |
| `python -m ruff format --check .` | Passed |
| `python -m compileall -q main.py scrapers scripts` | Passed |
| `python -m pip check` | No broken requirements |
| `git diff --check` | Passed |

Coverage includes both table layouts/multiple tables, optional/unknown prices,
Unicode/Indian currency, name normalization, duplicate/conflicting GMP, permission
gates, fallback/priority, changed headers, robots allow/disallow/crawl pacing,
403/404/429/5xx, timeouts, backoff and Retry-After seconds/date, redirect refusal,
RSS dedup/tags/limits/malformed feeds, OHLCV validation, MultiIndex handling,
timezones, Wilder RSI/SMA warm-up, rate limits, atomic export failure, null/empty
CSV/JSON, snapshots, CLI subprocesses and failure isolation, IPO import validation.
Fixtures are synthetic and tests use mocked transport/prices; there are no
live integration tests hidden in the offline suite.

## Live checks actually executed

Research and runtime checks were carried out on 12 November IST
(11 November UTC). No live requests were made to a restricted GMP or exchange data
endpoint. The source-policy research is in `SOURCE_STATUS.md`.

Initial `python scripts/verify_live.py --personal-use`:

- Economic Times: robots check succeeded; RSS parsed 30 metadata records.
- Mint: robots check succeeded; advertised `/rss/marketsRSS` returned HTTP 404.
  It was removed from default enabled feeds. Not marked working.
- Yahoo/yfinance: returned 13 validated rows across RELIANCE.NS, RELIANCE.BO,
  Nifty and Sensex. An initial library connection warning recovered. Invalid bars
  were logged. The collector was then improved to surface rejected bars as partial
  results rather than simply logging them. This initial live report's `passed`
  label must not be interpreted as complete date coverage.
- Script exit code: 1 because Mint failed; this is not a fully passed live suite.

After the validation/reporting fix, the actual CLI command executed was:

```bash
python main.py --all --acknowledge-rss-terms
```

| Collector | Result | Valid records | Detail |
| --- | --- | --- | --- |
| GMP | Intentionally disabled | 0 | InvestorGain/IPOWatch permissions not established |
| Stocks/indices | Partial live success | 21 | RELIANCE.NS 4, TCS.NS 4, INFY.NS 4, RELIANCE.BO 1, Nifty 4, Sensex 4 |
| News | Passed live fetch/parser/export | 30 | Economic Times; metadata only, personal use |
| IPO | Intentionally empty | 0 | No authorized local metadata file supplied |

The CLI finished all four collectors and wrote CSV/JSON category files, legacy
files and the run summary. Exit code 1 correctly reported five rejected invalid
OHLC bars for 11 November, one each from RELIANCE.NS, TCS.NS, INFY.NS, Nifty and
Sensex. Those observations were not repaired, invented or exported. BSE returned
one valid bar; completeness of historical coverage is not guaranteed. Source
requests were sequential, with timeouts/pacing and no bypasses.

Live data remains under ignored `data/` paths, not committed. No article text,
raw publisher HTML or scraped datasets are included in the release. The live
verification script is opt-in and never used by CI.

## Compatibility and remaining limits

Python 3.10–3.13 are configured as separate CI jobs. Local execution above is
Python 3.12; consult GitHub Actions for the pushed commit before claiming the other
versions passed. Fresh dependency resolution is not a lockfile/reproducibility
promise. APIs, terms, markup and availability can change.

No permitted live GMP adapter was demonstrated. Generic mapping support is
synthetic-tested, not a claim that a restricted provider works. Official IPO web
collection is unavailable; normalized local import is the supported alternative.
Mint, Business Standard and Moneycontrol are not enabled. ET data must not be
republished/redistributed without permission. Yahoo data is unofficial, delayed or
revised, and personal-use rights do not imply commercial redistribution rights.
