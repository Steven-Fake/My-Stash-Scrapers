import asyncio
import unittest
from py_common.types import PerformerSearchResult
from scrapers import GalleryEpic
import json


class GalleryEpicTest(unittest.TestCase):

    def test_parse_performer_by_url(self):
        scraper = GalleryEpic()
        result = scraper.parse_performer_by_url(
            PerformerSearchResult(url="https://galleryepic.com/zh/coser/385/1", name="")
        )

        print(json.dumps(result, ensure_ascii=False))

        self.assertEqual(result["name"], "千猫猫")
        self.assertEqual(result["image"], "https://static.galleryepic.xyz/image/b97f5f51-b71e-4ddf-a77d-511f9f99fee4")
        self.assertIn("https://www.weibo.com/u/5931091136", result["urls"])

    def test_parse_performer_by_name(self):
        scraper = GalleryEpic()
        result = asyncio.run(scraper.parse_performer_by_name(info=PerformerSearchResult(name="千猫猫", url="")))

        print(json.dumps(result, ensure_ascii=False))

        self.assertIsNotNone(result)


if __name__ == '__main__':
    unittest.main()
