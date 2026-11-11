"""Offline synthetic fixtures; no network access or third-party data."""
import unittest
from unittest.mock import Mock
import requests
from scrapers.gmp_scraper import GMPSource, parse_gmp_html, _money, _robots_allowed


class GMPTests(unittest.TestCase):
    def setUp(self):
        self.source = GMPSource("Fixture", "https://example.org/ipo-gmp", "#gmp")

    def test_money(self):
        self.assertEqual(_money("₹1,250"), 1250.0)
        self.assertEqual(_money("-₹12.50"), -12.5)
        self.assertEqual(_money("0"), 0.0)

    def test_ambiguous_values_not_guessed(self):
        for value in ("expected ₹100", "₹100-120", "N/A", "", "10%", "₹1,000 (est.)"):
            with self.subTest(value=value):
                self.assertIsNone(_money(value))

    def test_parse_verified_layout(self):
        html = '<table id="gmp"><tbody><tr><td>Sample IPO</td><td>₹125</td></tr></tbody></table>'
        rows = parse_gmp_html(html, self.source)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["gmp_inr"], 125.0)
        self.assertEqual(rows[0]["ipo_name"], "Sample IPO")
        self.assertEqual(rows[0]["source_url"], self.source.url)
        self.assertIn("retrieved_at_utc", rows[0])

    def test_missing_table_returns_no_rows(self):
        self.assertEqual(parse_gmp_html("<p>No table</p>", self.source), [])

    def test_invalid_rows_are_skipped(self):
        html = '<table id="gmp"><tbody><tr><td>IPO</td><td>NA</td></tr><tr><td>Incomplete</td></tr></tbody></table>'
        self.assertEqual(parse_gmp_html(html, self.source), [])

    def test_custom_column_mapping(self):
        src = GMPSource("Fixture", "https://example.org/ipo-gmp", "#gmp", "tr", 1, 2)
        html = '<table id="gmp"><tr><th>id</th><th>name</th><th>gmp</th></tr><tr><td>1</td><td>IPO</td><td>₹42</td></tr></table>'
        self.assertEqual(parse_gmp_html(html, src)[0]["gmp_inr"], 42.0)

    def test_robots_disallow(self):
        session = Mock()
        response = Mock(text="User-agent: *\nDisallow: /ipo-gmp\n")
        response.raise_for_status.return_value = None
        session.get.return_value = response
        self.assertFalse(_robots_allowed(session, self.source.url, "open-market-insights"))

    def test_robots_allow(self):
        session = Mock()
        response = Mock(text="User-agent: *\nAllow: /\n")
        response.raise_for_status.return_value = None
        session.get.return_value = response
        self.assertTrue(_robots_allowed(session, self.source.url, "open-market-insights"))

    def test_robots_network_failure_fails_closed(self):
        session = Mock()
        session.get.side_effect = requests.Timeout("timed out")
        self.assertFalse(_robots_allowed(session, self.source.url, "open-market-insights"))


if __name__ == "__main__":
    unittest.main()
