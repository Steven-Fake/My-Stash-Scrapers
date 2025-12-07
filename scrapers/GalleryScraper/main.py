import asyncio
import json
import sys
from urllib.parse import urlsplit

from py_common import log
from py_common.deps import ensure_requirements
from py_common.types import ScrapedPerformer, PerformerSearchResult
from scrapers import GalleryEpic, V2PH, XChina
from utils import jaccard_similarity

ensure_requirements("bs4:beautifulsoup4", "requests")

all_scrapers = [
    GalleryEpic, V2PH, XChina
]


def performer_by_url(url_info: PerformerSearchResult) -> ScrapedPerformer:
    if not url_info.get("url"):
        log.error("No URL provided")
        sys.exit(-1)

    domain = urlsplit(url_info["url"]).netloc.lower()

    for scraper_cls in all_scrapers:
        if domain in scraper_cls.domain:
            scraper = scraper_cls()
            return scraper.parse_performer_by_url(url_info)
    else:
        log.error(f"No scraper found for domain: {domain}\n")
        sys.exit(-1)


async def performer_by_name(name_info: PerformerSearchResult) -> list[PerformerSearchResult]:
    if not name_info.get("name"):
        log.error("No name provided")
        sys.exit(-1)

    tasks = [
        scraper_cls().parse_performer_by_name(name_info)
        for scraper_cls in all_scrapers
    ]
    resp = await asyncio.gather(*tasks)
    result: list[PerformerSearchResult] = [item for sub in resp for item in sub]
    result.sort(key=lambda p: jaccard_similarity(p.get("name", ""), name_info.get("name")), reverse=True)
    return result

if __name__ == "__main__":
    info = json.loads(sys.stdin.read())

    if sys.argv[1] == "performerByURL":
        result = performer_by_url(info)
        print(json.dumps(result, ensure_ascii=False))

    elif sys.argv[1] == "performerByName":
        result = asyncio.run(performer_by_name(info))
        print(json.dumps(result, ensure_ascii=False))
