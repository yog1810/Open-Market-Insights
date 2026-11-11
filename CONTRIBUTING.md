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
permission/reuse scope, attribution, robots handling, source status and layout-change
tests. A successful HTTP response alone is insufficient. Leave uncertain sources
disabled. Never work around access restrictions.

Describe behavior changes, executed checks and remaining limitations in a pull
request. Live tests are manual, opt-in, and only for permitted personal use:
`python scripts/verify_live.py --personal-use`. Do not turn this into scheduled
scraping without a fresh permission review. Source configs must contain a public,
non-secret permission reference. Use issues to report reproducible bugs without
posting restricted third-party data.
