import unittest

from scrapers import V2PH


class V2PHTest(unittest.TestCase):

    def test_parse_performer_by_url(self):
        scraper = V2PH()
        result = scraper.parse_performer_by_url({"url": "https://www.v2ph.com/actor/Erzuoxxxx"})

        self.assertEqual(result["name"], "二佐Nisa")
        self.assertIsNotNone(result["image"])
        self.assertIn("https://weibo.com/u/6516812442", result["urls"])


if __name__ == '__main__':
    unittest.main()
