import unittest
from scrapers.gmp_scraper import GMPSource, parse_gmp_html, _money


class GMPTests(unittest.TestCase):
    def test_money(self):
        self.assertEqual(_money("₹1,250"), 1250.0)
        self.assertIsNone(_money("expected ₹100"))

    def test_parse_verified_layout(self):
        html = '<table id="gmp"><tbody><tr><td>Sample IPO</td><td>₹125</td></tr></tbody></table>'
        src = GMPSource("Test", "https://example.org/gmp", "#gmp")
        rows = parse_gmp_html(html, src)
        self.assertEqual(rows[0]["gmp_inr"], 125.0)
        self.assertEqual(rows[0]["ipo_name"], "Sample IPO")


if __name__ == "__main__":
    unittest.main()
