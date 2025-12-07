import asyncio
import json
import unittest
from py_common.types import PerformerSearchResult
from scrapers import XChina


class XChinaTest(unittest.TestCase):

    def test_parse_performer_by_url(self):
        scraper = XChina()
        result = scraper.parse_performer_by_url(
            PerformerSearchResult(url="https://xchina.co/model/id-5f7f8f29e30e2.html", name="")
        )

        print(json.dumps(result, ensure_ascii=False))

        self.assertEqual(result["name"], "小丁Ding")
        self.assertEqual(result["birthdate"], "1999-02-10")
        self.assertIsNotNone(result["country"])
        self.assertIsNotNone(result["details"])
        self.assertIsNotNone(result["image"])

    def test_parse_performer_by_name(self):
        scraper = XChina()
        result = asyncio.run(scraper.parse_performer_by_name(info=PerformerSearchResult(name="小丁", url="")))

        print(json.dumps(result, ensure_ascii=False))

        self.assertIsNotNone(result)


if __name__ == '__main__':
    unittest.main()
