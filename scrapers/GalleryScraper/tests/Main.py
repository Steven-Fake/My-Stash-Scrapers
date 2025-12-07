import asyncio
import json
import unittest

from main import performer_by_name
from py_common.types import PerformerSearchResult


class Main(unittest.TestCase):
    def test_parse_performer_by_name(self):
        result = asyncio.run(performer_by_name(PerformerSearchResult(name="小丁", url="")))

        print(json.dumps(result, ensure_ascii=False))

        self.assertIsNotNone(result)


if __name__ == '__main__':
    unittest.main()
