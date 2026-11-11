# Repository audit and implementation notes

Base commit: `c39e21b`. Review date: 12 November 2026 (IST).
All original Python modules/tests, README, dependency declarations, license, source
config, ignore rules and Actions workflow were read before edits.

| Finding | Resolution |
| --- | --- |
| GMP sources were homepages with illustrative selectors | Removed homepage scraping; explicit disabled descriptors and permission-evidenced configurable adapter |
| HTTP had no retries and paced between sources rather than per host/request | Shared paced client, bounded backoff, Retry-After, robots cache/crawl directives, timeout and redirect refusal |
| Direct GMP API could collect arbitrary source without permission gate | Permission gate applies in collector, not only config loader |
| GMP schema lacked issuer keys/optional prices/conflict handling | Conservative Unicode keys, raw GMP/source retention, null derived values, duplicate/disagreement flags |
| News used an outdated Mint candidate and enabled Business Standard on blanket acknowledgement | Tested official Mint candidate (404), disabled it; excluded restricted BS and unknown Moneycontrol; only ET default after opt-in |
| Market prices accepted invalid/missing OHLC and had no retry/error summary | Validated bars, UTC daily dates, retries, rate-limit stopping and partial-result diagnostics |
| No IPO command/import | Added normalized local metadata import; no prohibited exchange scraping |
| Exports directly overwrote files and empty schemas varied | Per-file atomic UTF-8 writes, null/empty schemas, snapshots/category and legacy paths |
| CLI hid failures behind successful exit | Isolated collectors with explicit partial/failure summary and nonzero exit |
| Only nine offline tests and Python 3.11 CI | Expanded pytest coverage and Python 3.10–3.13 CI matrix with lint/artifact reports |

Public `main.py` flags, original `scrapers.gmp_scraper` imports and legacy output
paths are preserved. The working market/RSS parsers were extended without changing
their core responsibility. Permission requirements were intentionally tightened.
Source observations retain supplied status; discrepancy is a separate flag, so a
conflict does not erase a source's original IPO status. Source dates lacking full
timezone/year context remain raw. The GMP table parser skips ambiguous/missing
values instead of treating missing as a zero observation.

The tool is modular, but does not promise complete market coverage, an authorized
public-data republication service, a commercial feed or automatic issuer matching.
