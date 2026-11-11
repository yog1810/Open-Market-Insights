# open-market-insights

Free, modular Python collection of **Indian market data**, including an extensible IPO grey market premium (GMP) adapter, stock/index prices and financial news RSS metadata. MIT licensed.

> **IMPORTANT:** GMP is unofficial, unregulated, sometimes inaccurate, and not an exchange-provided price. This project is educational software, **not financial advice, investment research, or a trading recommendation**. Never rely on GMP alone to make an IPO decision. Yahoo Finance data may be delayed or revised. Respect each publisher's terms, robots.txt, copyright and licensing; public visibility does **not** automatically grant scraping or redistribution rights. The MIT license applies to this code, **not third-party data**.

## Install

Python 3.10+ recommended.

```bash
git clone https://github.com/yog1810/Open-Market-Insights.git
cd Open-Market-Insights
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py --all
```

Or run `python main.py` (same default). RSS collection is disabled by default until the user explicitly acknowledges the publisher terms. Results appear in `data/` as CSV and JSON. `data/` output is ignored by Git.

## CLI

```bash
python main.py --stocks --symbols RELIANCE.NS TCS.NS ^NSEI ^BSESN --period 1mo
python main.py --news --acknowledge-rss-terms
python main.py --gmp
python main.py --all --output data --verbose --acknowledge-rss-terms
python -m unittest discover -s tests -v
```

Use `.NS` for NSE, `.BO` for BSE, `^NSEI` for Nifty 50, and `^BSESN` for Sensex. The stock provider is the unofficial `yfinance` client, not an exchange feed.

## Source review (12 November 2026)

- IPOWatch public GMP page: https://ipowatch.in/ipo-grey-market-premium-latest-ipo-gmp/ — discovered, but automated access permission and HTML selectors are **not verified**.
- Economic Times official RSS terms: https://economictimes.indiatimes.com/rss.cms — personal use only; aggregation/redistribution requires permission.
- Mint official RSS terms: https://www.livemint.com/rss — personal, noncommercial newsreader use.
- Business Standard RSS directory: https://www.business-standard.com/rss-feeds/listing — review terms and feed endpoints.
- The RSS flag `--acknowledge-rss-terms` is an explicit opt-in for permitted personal use, **not** a license to redistribute publisher content.
- No live network integration tests have been completed. Tests use synthetic fixtures.

## GMP setup (manual verification required)

`--gmp` **does not return live GMP out of the box**. This is intentional: the two source definitions currently point to homepages, and generic HTML table selectors are illustrative only. The program skips those placeholders rather than creating misleading data.

1. Check Chittorgarh.com and IPOWatch.in terms, robots.txt, and whether automated collection and your intended reuse are allowed. Obtain permission when needed. Do not evade paywalls, CAPTCHAs, access restrictions, or rate limits.
2. Find a current, permitted public GMP listing URL on each website; update `SOURCES` in `scrapers/gmp_scraper.py`.
3. Inspect the page's HTML manually, identify the correct table/row selectors and IPO name/GMP column indices, then update the `GMPSource` configuration. Check for JavaScript-only pages, changed columns, and units.
4. Run `python main.py --gmp`, inspect `data/gmp.csv`, and compare every parsed value with the source. Do not publish scraped data until accuracy and redistribution rights are confirmed.

The collector checks robots.txt (fails closed when unavailable), uses a descriptive User-Agent, sleeps at least one second between configured sources, sets request timeouts and logs failures. Replace `set-your-email` in User-Agent with a real project contact before enabling scraping. Additional per-host crawl-delay and terms may require a longer interval; configure accordingly. `robots.txt` is **not** a substitute for site terms or permission.

## RSS setup

`news_insights.py` includes *candidate* RSS feed URLs for Economic Times, Mint and Business Standard; availability, robots policy, and reuse rights are not guaranteed. Moneycontrol is intentionally left as a TODO until an approved current feed URL is confirmed. The aggregator stores only headlines, links, publication times and publisher attribution, not full articles. Verify the publisher's rules before redistribution. Invalid or blocked feeds are skipped with warnings.

## Outputs

- `data/gmp.csv`, `data/gmp.json` — verified IPO names, GMP in INR, source and UTC retrieval timestamp; empty until configured.
- `data/market_data.csv`, `data/market_data.json` — OHLCV history by ticker and date.
- `data/news.csv`, `data/news.json` — deduplicated RSS metadata.

CSV and JSON are overwritten on each run. Empty datasets produce empty files, not invented observations. To build a historical archive, add date-stamped output filenames or a database.

## Extend the project

Each scraper exposes a `collect_*()` function returning a `pandas.DataFrame`. Add a new adapter in `scrapers/`, include clear source attribution and timestamps, implement timeouts/robots/terms checks for HTTP fetching, and register it in `main.py`. Keep selectors in source configuration, add tests with **synthetic** HTML/XML fixtures, and avoid committing third-party copyrighted datasets.

Contributions: fork, create a feature branch, run `python -m unittest discover -s tests -v`, open a PR describing source permissions, sample output schema and error behavior. Issues and corrections welcome. Do not submit credentials or copied full articles.

## Limitations and responsible use

This is a starter toolkit, not a production trading feed or a claim of working live GMP coverage. Source markup and RSS endpoints can change; financial providers can rate-limit or block requests. Verify all data independently. Use a sensible schedule, avoid aggressive parallelism, follow each site's terms and licensing, and obtain independent legal/compliance advice for commercial use or redistribution. No SEBI/NSE/BSE affiliation or endorsement is claimed.
