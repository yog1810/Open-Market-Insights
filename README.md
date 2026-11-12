# Open Market Insights

Free, modular Indian market data toolkit for personal education and research.
Python 3.10–3.13 target • MIT code license • CSV/JSON exports • Offline tests

**GMP collection is enabled by default through IPOReports' public table.**
Run `python main.py --gmp`. This fetches the first listing page for personal
informational research, retains source update strings/status and skips unavailable
values. Listed IPO observations may be old; a successful fetch does not make them
current tradable quotes. Yahoo historical prices are unofficial and may be delayed
or revised. This project is not financial advice or an exchange feed.

## Install

```bash
git clone https://github.com/yog1810/Open-Market-Insights.git
cd Open-Market-Insights
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows PowerShell instead: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py --all
```

No paid API keys or `.env` loader are required. Yahoo's terms govern personal use
of retrieved prices. The MIT license does not license third-party data.

## Commands

```bash
python main.py --all
python main.py --gmp
python main.py --stocks
python main.py --news
python main.py --ipo
python main.py --all --verbose
python main.py --gmp --source investorgain
python main.py --gmp --gmp-config gmp_sources.example.json
python main.py --stocks --symbols RELIANCE.NS TCS.NS INFY.NS RELIANCE.BO ^NSEI ^BSESN --period 1mo
python main.py --stocks --period 3mo --indicators --snapshot
python main.py --news --acknowledge-rss-terms --source "Economic Times" --keywords IPO Nifty --limit 10
python main.py --ipo
python main.py --ipo --ipo-file authorized_ipo_metadata.csv
```

No flag means `--all`. Categories are mutually exclusive; `--all` runs each in
isolation. One collector failure does not stop the others. Exit code 1 means a
collector/source failed or returned a partial result; 0 includes intentionally
empty/disabled collectors. See `data/logs/run_summary.json` and stderr for details.
An unknown `--source` fails explicitly. For GMP, this flag selects a configured
provider; it does not override permissions. IPOReports is enabled. InvestorGain/IPOWatch
entries remain explicitly disabled for published restrictions/unverified mappings; Chittorgarh has no verified listing adapter.

RSS requires `--acknowledge-rss-terms` even at API level (`permission_reviewed=True`).
Only ET is enabled after the runtime check; Mint's advertised feed returned 404 and is excluded from defaults. The flag grants
no redistribution, hosting or commercial rights. Do not use this to populate a
public news site. Business Standard/Moneycontrol are excluded from defaults.

## What is implemented

- GMP adapters: explicit table/row/column mappings and a verified IPOReports parser;
  configurable priority (config list order), fallback after errors, duplicate
  detection and retained disagreements. No averages or fabricated missing values.
- HTTP: descriptive User-Agent, HTTPS, fail-closed robots checks, per-host pacing,
  Crawl-delay/Request-rate, timeout, bounded exponential retry and Retry-After.
  Redirects require independent review; no automatic following. Retry-After over
  60 seconds stops the run's source instead of retrying prematurely.
- Stocks/indices: daily unadjusted OHLCV; missing/invalid price rejection, nullable
  volume, UTC normalization, per-symbol errors, optional SMA20/SMA50/Wilder RSI14
  and daily percentage change. Warm-up values are null. No real-time claims.
- News: RSS/Atom metadata parsing, URL deduplication, source/keyword filtering,
  IPO detection, UTC publication times; no full articles or descriptions exported.
- IPO metadata: validated CSV/JSON import of lawfully obtained normalized records.
  No NSE website scraper (terms prohibit it), no unverified BSE API.
  With no `--ipo-file`, `--ipo` now collects the documented Xflot public IPO API,
  exports an IPO registry/calendar/subscription totals, and keeps SQLite history.
- Storage: consistent empty schemas, UTF-8, null JSON values, duplicate removal,
  atomic replacement per file, optional UTC snapshots and run summaries.

## Source status and licensing

See [source status table, review dates and primary evidence](docs/SOURCE_STATUS.md).
See [executed tests and live verification results](docs/VALIDATION.md).
A reachable page or robots Allow does not grant permission. Obtain written
permission where required. Do not bypass CAPTCHAs, paywalls, authentication,
Cloudflare, restrictions or rate limits. No SEBI/NSE/BSE affiliation is claimed.

## Configuring an authorized GMP provider

Copy `gmp_sources.example.json`, replace its example URL and map inspected
selectors/columns, then set `enabled: true`. Separate written-permission
attestation is no longer required by the software. The legacy
`permission_reviewed`/`permission_reference` fields are accepted as inert metadata
for compatibility; they no longer decide whether GMP collection runs.
Respect explicit restrictions, source terms, robots and rate limits. `expected_headers`
contains the exact lower-case sequence of selected table headers for drift checking.
Only map `issue_price_cell` when it means a confirmed single per-share issue price;
price-band ranges are rejected. `updated_cell` remains raw without an invented year
or timezone. Config order is priority; `--fallback-only` stops at the first valid
source and cannot compare sources not fetched.

Normalized GMP fields:

```text
ipo_name, ipo_slug, gmp_inr, raw_gmp, issue_price, estimated_listing_price,
estimate_basis, gmp_percentage, source, source_url, source_updated_at,
retrieved_at_utc, status, discrepancy, raw_issue_price, subscription_status
```

`estimated_listing_price = issue_price + gmp_inr` is an unofficial calculation,
not a prediction. It is null without an unambiguous positive issue price. Zero
GMP is valid; missing, ranges and commentary are skipped/logged. All conflicting
GMP observations remain present with `discrepancy=true`; comparisons are not a
freshness guarantee. Names are candidate keys, not proof of company identity.

The old `scrapers.gmp_scraper` imports remain supported. Sources use an explicit
`enabled` flag; there is no blanket permission-uncertainty gate. IPOReports parses
its GMP amount separately from its percentage and preserves the full raw cell.
Its issue-price ranges are stored in `raw_issue_price`; no final issue price or
derived listing estimate is guessed. Only the first page is collected, with
no automatic pagination or scheduled polling.

## IPO registry and calendar

`python main.py --ipo` uses https://www.xflot.com/api-docs, carries its original
response disclaimer and source link, and uses a 60-second per-host interval.
It is third-party reported data, not an official NSE/BSE feed. The response limit
is 200; completeness of the entire IPO market is not claimed.

Outputs under `data/ipo/`: `ipo.csv/json`, `calendar.csv/json`,
`subscriptions.csv/json`, `ipo_conflicts.csv/json`, `excluded_records.csv/json`, and `ipo_registry.sqlite`.
The registry preserves observation history and provider variants transactionally.
NCD/ZCZP/FPO/social enterprise and explicitly withdrawn/postponed issues are
excluded from the IPO view, with an exclusion report rather than invented statuses.
When repeated provider slugs disagree, the current view picks the most complete
record (then latest provider update), marks it `record_conflicted`, and preserves
**all** conflicting observations separately and in SQLite. A preferred row is not
proof of which variant is correct. Calendar events inherit the conflict flag.
Do not automatically promote conflicted provider records into editorial pages.

Dates, lot sizes, issue sizes (explicitly crore), price bands, listing observations,
sector and registrar metadata remain nullable. `source_updated_at` is a record
update; the bulk API does not establish GMP or subscription observation times.
Those separate timestamps remain null. Never substitute fetch time for quote time.
The current endpoint's per-issue detail was checked too: the sampled issue
returned empty GMP history/category subscription arrays, so no category figures
were invented. Company financial statements are not supplied by this endpoint.

## IPO import schema

Required fields: `ipo_name`, `exchange` (`NSE`, `BSE`, `NSE/BSE`), `source_url`.
Optional fields: `open_date`, `close_date`, `listing_date` (YYYY-MM-DD),
`price_band_low`, `price_band_high`, `lot_size`, `status`. Missing fields stay null.
`ipo_slug` and UTC import timestamp are generated. The importer validates syntax
and ranges, but does not authenticate the supplied provenance. It does not mark
GMP as official or automatically join companies on fuzzy name matches.

## Output paths

```text
data/
  gmp/gmp.csv                 gmp/gmp.json
  ipo/ipo.csv                 ipo/ipo.json
  stocks/stocks.csv           stocks/stocks.json
  indices/indices.csv         indices/indices.json
  news/news.csv               news/news.json
  logs/run_summary.csv        logs/run_summary.json
```

Legacy `data/gmp.*`, `data/news.*`, `data/market_data.*` remain available.
Default files are replaced; `--snapshot` appends a UTC timestamp. Empty CSVs retain
headers; empty JSON is `[]`. Atomic replacement is per file, not a transaction
across the CSV/JSON pair or a concurrent-writer database. Generated data and logs
are ignored by Git; never force-add them. Historical naive daily bars are treated
as Asia/Kolkata midnight and converted to UTC; aware timestamps preserve the actual
instant. Choose enough price history for indicator warm-up (50 bars for SMA50).

## Development and verification

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
# Manual opt-in, personal use only; no blocked GMP/exchange source requests:
python scripts/verify_live.py --personal-use
```

CI runs offline tests on Python 3.10, 3.11, 3.12 and 3.13. Synthetic fixtures do
not establish live provider compatibility. The previous unittest command still
runs the original nine tests, but pytest is required for the full suite.

## Troubleshooting

- Empty IPO output is expected without a local import. Empty GMP output means no
  valid records were found, collection failed, or configured sources are disabled.
- Check `data/logs/run_summary.json` for `failed`, `partial`, `empty_or_disabled`.
- Robots 403/404/unavailable/malformed: fail closed; obtain clarification from the
  source. This project deliberately does not interpret missing robots as permission.
- Layout change: re-inspect permitted markup and update mappings/tests; do not
  loosen selectors until arbitrary unrelated tables parse.
- HTTP 429: honor Retry-After; reduce frequency. Yahoo rate limits stop that ticker.
- No prices/DNS/TLS/network denial: collection remains unverified; there is no
  synthetic-data fallback. Correct connectivity; do not evade access controls.
- Missing indicator: retrieve a longer period. Missing dates are not forward-filled.
- UTF-8 CSV: use your spreadsheet application's UTF-8 import option if needed.

Contributions: [CONTRIBUTING.md](CONTRIBUTING.md). Changes:
[CHANGELOG.md](CHANGELOG.md). Code license: [MIT](LICENSE).
