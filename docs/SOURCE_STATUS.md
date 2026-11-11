# Source review — 12 November 2026 (IST)

This is a permission and availability review, not a legal opinion. A discoverable
page, a search-engine snippet, a 200 response or robots Allow is not a data license.
The MIT license covers this repository's code only. No publisher datasets are
included. No CAPTCHA, access-control, browser impersonation override, proxy rotation,
undocumented exchange endpoint or login workaround is implemented by this toolkit.

| Source | Data | Automated access / reuse assessment | Checked | Implementation | Limitations |
| --- | --- | --- | --- | --- | --- |
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

No source met the permission standard for a live GMP extraction. Consequently,
no live adapter is represented as verified. Search rendering of IPOWatch displayed
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

Obtain appropriate permission; record a non-secret reference in
`permission_reference`; set `permission_reviewed` to JSON `true`; inspect the actual
permitted HTML; supply precise selectors, numeric column mappings and headers.
The list order defines priority. Runtime robots checks still apply. Explicit
permission config is an attestation, not automatic proof of permission.

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
