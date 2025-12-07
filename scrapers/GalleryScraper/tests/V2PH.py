import asyncio
import json
import unittest

from py_common.types import PerformerSearchResult
from scrapers import V2PH


class V2PHTest(unittest.TestCase):

    def test_parse_performer_by_url(self):
        scraper = V2PH()
        result = scraper.parse_performer_by_url(
            PerformerSearchResult(url="https://www.v2ph.com/actor/Erzuoxxxx", name="")
        )

        print(json.dumps(result, ensure_ascii=False))

        self.assertEqual(result["name"], "二佐Nisa")
        self.assertIsNotNone(result["image"])
        self.assertIn("https://weibo.com/u/6516812442", result["urls"])

    def test_parse_performer_by_name(self):
        scraper = V2PH()
        result = asyncio.run(scraper.parse_performer_by_name(info=PerformerSearchResult(name="二佐Nisa", url="")))

        print(json.dumps(result, ensure_ascii=False))

        self.assertIsNotNone(result)


if __name__ == '__main__':
    unittest.main()
