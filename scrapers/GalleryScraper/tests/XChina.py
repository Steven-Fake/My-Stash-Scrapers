import unittest

from scrapers import XChina


class XChinaTest(unittest.TestCase):

    def test_parse_performer_by_url(self):
        scraper = XChina()
        result = scraper.parse_performer_by_url({"url": "https://xchina.co/model/id-5f7f8f29e30e2.html"})
        self.assertEqual(result["name"], "就是阿朱啊")
        self.assertIsNotNone(result["image"])
        self.assertEqual(result["birthdate"], "1997-08-20")
        self.assertIsNotNone(result["details"])


if __name__ == '__main__':
    unittest.main()
