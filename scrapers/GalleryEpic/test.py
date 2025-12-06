import unittest

from GalleryEpic import parse_performer_by_url


class GalleryEpicTest(unittest.TestCase):

    def test_parse_performer_by_url(self):
        result = parse_performer_by_url({"url": "https://galleryepic.com/zh/coser/385/1"})

        self.assertEqual(result["name"], "千猫猫")
        self.assertEqual(result["image"], "https://static.galleryepic.xyz/image/b97f5f51-b71e-4ddf-a77d-511f9f99fee4")
        self.assertIn("https://www.weibo.com/u/5931091136", result["urls"])


if __name__ == '__main__':
    unittest.main()
