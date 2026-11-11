# Contributing

Create a focused branch and preserve public imports/CLI flags where practical.
Python 3.10–3.13 is the supported target. Install development dependencies:

```bash
python -m pip install -r requirements-dev.txt
python -m ruff check .
python -m ruff format --check .
python -m pytest -q
```

Unit tests must be offline, with synthetic HTML/XML/prices and mocked transport.
Never add copied article bodies, raw publisher pages, scraped datasets, API keys,
private permission correspondence or credentials. New sources need documented
terms/reuse scope, attribution, robots handling, source status and layout-change
tests. A successful HTTP response alone does not grant redistribution rights.
Use explicit source enablement, not a blanket written-permission requirement. Never work around access restrictions.

Describe behavior changes, executed checks and remaining limitations in a pull
request. Live tests are manual, opt-in, and only for permitted personal use:
`python scripts/verify_live.py --personal-use`. Do not turn this into scheduled
scraping without a fresh permission review. Do not include private permission documents in source configuration. Use issues to report reproducible bugs without
posting restricted third-party data.
