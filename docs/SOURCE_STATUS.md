# Source review — 12 November 2026 (IST)

This is a permission and availability review, not a legal opinion. A discoverable
page, a search-engine snippet, a 200 response or robots Allow is not a data license.
The MIT license covers this repository's code only. No publisher datasets are
included. No CAPTCHA, access-control, browser impersonation override, proxy rotation,
undocumented exchange endpoint or login workaround is implemented by this toolkit.

| Source | Data | Automated access / reuse assessment | Checked | Implementation | Limitations |
| --- | --- | --- | --- | --- | --- |
| IPOReports | Public unofficial GMP | Enabled for low-volume personal informational research; terms prohibit abusive scraping and substantial republication | 2026-11-12 | Live-tested first-page parser with exact headers | Source timestamps/status retained; some rows historical/listed; no redistribution license or full market coverage |
| Xflot public API | IPO registry, calendar dates, bands, lots, subscription totals and listing metadata | Documented public API: attribution, response disclaimer, no more than one poll/minute | 2026-11-12 | Live-tested; 183 returned rows, 121 IPO-only preferred records, all variants retained | 32 IPO slugs had conflicting variants; 27 non-IPO/withdrawn rows excluded; quote/subscription observation timestamps and financial statements unavailable |
| InvestorGain | Unofficial GMP | Disabled; written permission required under published IP restrictions | 2026-11-12 | Disabled source descriptor; synthetic-tested configurable table parser | Current GMP page discovered, live HTML/CSS not verified; robots endpoint unavailable to research tool |
| IPOWatch | Unofficial GMP | Disabled; terms restrict downloading/copying/republication | 2026-11-12 | Disabled descriptor; no claimed live mapping | Listing tables visible in search rendering; live raw HTML/CSS and robots not verified; not collected |
| Chittorgarh | IPO data; possible GMP | Disabled; robots blocked research access, permission unknown | 2026-11-12 | Explicit unavailable descriptor, no placeholder homepage scraping | No verified GMP listing URL or selectors; no live access attempted around block |
| IPO Ji (alternative) | Unofficial GMP/history | Disabled; no automation/reuse permission established | 2026-11-12 | Research only | Public GMP history pages discovered; attempted terms URL unavailable; no data collected |
| NSE | Official IPO metadata | Website terms prohibit systematic automated collection | 2026-11-12 | No web adapter; normalized local import only | Public upcoming-issues page has company/security/start/end/status/subscription headers; body requires dynamic data; no private API calls |
| BSE | Official IPO metadata/data products | No free permitted automated IPO interface established | 2026-11-12 | No web adapter; normalized local import only | Official data-products portal offers subscription/trial products; attempted copyright page unavailable |
| Yahoo Finance / yfinance | Historical stock/index OHLCV | Unofficial library; intended personal research use, Yahoo terms govern data | 2026-11-12 | Mock-tested integration, bounded retries and validation | See live check below; delayed/revised, no redistribution license implied |
| Economic Times | RSS headlines/links/timestamps | Opt-in personal newsreader use; aggregation/redistribution/commercial use restricted | 2026-11-12 | RSS metadata parser; CLI opt-in required | Official RSS directory and robots reviewed; runtime check below; no article requests |
| Mint | RSS headlines/links/timestamps | Opt-in personal noncommercial newsreader use only | 2026-11-12 | Advertised feed tested; disabled after HTTP 404 | Official RSS directory and robots reviewed; advertised endpoint returned HTTP 404; no public feed republication |
| Business Standard | RSS | Disabled; terms prohibit automated collection without written consent | 2026-11-12 | Excluded from defaults | RSS directory is public; its existence does not override terms; endpoint not probed |
| Moneycontrol | RSS candidate | Disabled; permission and current English feed not established | 2026-11-12 | Excluded from defaults | Terms page found; English RSS directory unavailable; Hindi directory discovered, not collected |

## Primary evidence

- IPOReports public table: https://iporeports.in/
- IPOReports terms: https://iporeports.in/terms-and-conditions/
- IPOReports disclaimer: https://iporeports.in/disclaimer/


- InvestorGain GMP listing: https://www.investorgain.com/report/ipo-gmp-live/331/
- InvestorGain terms/IP restrictions: https://www.investorgain.com/article/disclaimer-and-privacy-statement/250/
- IPOWatch listing: https://ipowatch.in/ipo-grey-market-premium-latest-ipo-gmp/
- IPOWatch terms: https://ipowatch.in/term-of-use/
- IPO Ji public information: https://www.ipoji.com/ipo-glossary
- IPO Ji example history route: https://www.ipoji.com/ipo-gmp/bench-mark-infotech-services-ipo
- NSE upcoming issues: https://www.nseindia.com/market-data/all-upcoming-issues-ipo
- NSE terms (automated-collection prohibition): https://www.nseindia.com/static/nse-terms-of-use
- NSE data policy: https://www.nseindia.com/static/market-data/nse-data-policy
- BSE data products: https://marketdata.bseindia.com/
- yfinance project documentation/personal-use notice: https://ranaroussi.github.io/yfinance/
- ET RSS terms: https://economictimes.indiatimes.com/news/economy/rss.cms
- ET robots: https://economictimes.indiatimes.com/robots.txt
- ET candidate markets feed: https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms
- Mint RSS directory and specific terms: https://www.livemint.com/rss
- Mint robots: https://www.livemint.com/robots.txt
- Mint markets feed: https://www.livemint.com/rss/marketsRSS
- Business Standard terms: https://www.business-standard.com/terms-conditions
- Business Standard RSS directory: https://www.business-standard.com/rss-feeds/listing
- Moneycontrol terms: https://www.moneycontrol.com/cdata/termsofuse.php
- Moneycontrol Hindi RSS directory: https://hindi.moneycontrol.com/rss

## GMP HTML inspection and reliability limits

The initial release had no live GMP extraction. This was superseded by the
IPOReports adapter: its `#ipo-main-table` and 13-column header signature were
inspected from actual server-rendered HTML, including the mixed amount/percentage
GMP cell, name anchor, status badges and update column. The adapter stores only
table observations, not article text. IPOReports allows personal informational
research and prohibits abusive scraping; this is not a public redistribution license. Search rendering of IPOWatch displayed
Company, GMP, Trend, Price Band, Est. Gain and Date columns across separate
Mainboard/SME tables. That does not establish CSS selectors, server rendering,
per-IPO update times or whether a displayed price is the final issue price.
InvestorGain's current listing was discovered, but raw markup was not collected.
Chittorgarh's listing/markup remains unknown. Do not infer subscription status or
update timestamps from unrelated table cells or page publication dates.

The generic adapter supports explicit CSS/table mappings and optional exact header
signatures. It is tested against synthetic layouts, not copied publisher HTML.
Only set `issue_price_cell` for a single confirmed per-share INR issue price;
a range/upper price-band endpoint is not silently substituted. Ambiguous/missing
GMP rows are skipped with diagnostic logs, never converted to zero. A real zero GMP
is retained. Source update strings remain verbatim if their timezone/year is unknown.

## Enabling a source

Set `enabled: true` in a source config after inspecting its actual public layout.
The software no longer requires `permission_reviewed` or a written-permission
reference to collect GMP. Explicit site restrictions and runtime robots checks
still apply. Use low-volume personal research; obtain broader rights separately
for substantial republication or commercial redistribution. IPOReports performs
one listing-page fetch per run, with no automatic pagination or scheduled polling.

Default collection checks all enabled sources to retain discrepancies. Use
`--fallback-only` to stop after the first source returning valid observations;
that mode deliberately cannot compare sources that were not fetched.
Name normalization is conservative and retains company suffixes. Do not fuzzy-match
IPO companies without human review; identical normalized names are only candidates,
not evidence of issuer identity or that observations refer to the same date.

## Runtime live verification

The runtime checks and exact results are recorded in `docs/VALIDATION.md`. Source
policy research above succeeded through web research even when direct runtime
network access fails. These are separate claims. Blocked sources were not probed.

## Xflot registry extension

Documentation and published API conditions: https://www.xflot.com/api-docs

Bulk endpoint: https://www.xflot.com/api/public/market/ipos?limit=200

The public API supplies information for reuse with attribution and its disclaimer.
It does not make GMP official or guarantee accuracy. A sampled documented
per-issue endpoint returned no GMP history or category-wise subscription rows.
The database export preserves conflicting provider variants rather than silently
choosing them as independently verified issue terms.
